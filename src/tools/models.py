import re
import subprocess
import yaml
import random
import uuid
from .settings import *


class TerminalColors:
    WARNING = '\033[93m'
    END = '\033[0m'


class PermissionsLevel:
    NOOB = 1, 'n00b'
    ENTRY = 2, 'entry'
    MID = 3, 'mid'
    EXPERT = 4, 'expert'
    CUSTOM = 5, 'custom'
    RANDOM = random.randint(1, 5), 'random'


class Permissions:
    def __init__(self, level=PermissionsLevel.NOOB):
        # indicate the level of permissions.
        # this level is in the form of a tuple.
        # TODO define the permission for each level
        self.level, self.name = level


# "->" are function annotations. Normally used to know what is supposed to be the returned object type
def replace_variables(path: str, conf: object, tag: str = '!CONF') -> yaml.SafeLoader:
    # ${<VARIABLE>} | ${<VARIABLE><DEFAULT_SEPARATOR><default>}
    regex = '\${(\w+|\w+\\' + DEFAULT_SEPARATOR + '\w+)}.*?'
    pattern = re.compile(regex)
    loader = yaml.SafeLoader

    # the tag will be used to mark where to start searching for the pattern
    # e.g. key: !CONF ${IMPORTANT_VARIABLE} etc
    loader.add_implicit_resolver(tag, pattern, None)

    def constructor_var(loader_in, node):
        """
        This function is meant to replace the variables in the node from the yaml file with the value
        from the configuration file assigned.
        """
        value = loader_in.construct_scalar(node)
        match = pattern.findall(value)  # there might be more than one variable, so find them all

        if match:
            for group in match:
                # create an empty string as the default value
                # this value will be the replacement in case the variable is not included into the conf. file
                default = ''

                # split the group by ':', which defines the variable name and the default value, if given.
                # NOTE: this might be dangerous if the default value contains ':' as well! therefore, it is a
                # requirement of the file to include just one ':' in the whole variable.
                if DEFAULT_SEPARATOR in group:
                    variable, default = group.split(DEFAULT_SEPARATOR)
                else:
                    variable = group

                if variable == "UUID":
                    conf[variable] = str(uuid.uuid4())

                # replace the group with the value assigned to the key with name of the variable in the conf. file
                # if the variable is not found in the conf. file, the default value will be used instead
                value = value.replace(
                    f'${{{group}}}', conf[variable] if variable in conf else default
                )

        return value

    loader.add_constructor(tag, constructor_var)

    if path:
        with open(path) as data:
            yaml_data = yaml.load(data, Loader=loader)
            return yaml_data


# Use this class only for debugging
class Loader:
    """
    This class is meant to initialize the default parameters for a TTP given a target and, optionally,
    the permission level.
    Permissions refers to the capabilities allowed for the given level i.e. NOOB, level 0, will only be able to run
    the first set of commands from the ability.
    """

    def __init__(self, target, level=PermissionsLevel.NOOB, abilities_path='abilities.yml', conf_path='conf.yml'):
        self.target = target
        self.permissions = Permissions(level)
        self.abilities = (abilities_path, conf_path, self.permissions)

    @property
    def abilities(self):
        return self.abilities_

    @abilities.setter
    def abilities(self, init_vector: tuple):
        # separate the tuple into the path, configuration with the variables for the abilities.yaml file
        # and the permissions allowed for the given level.
        path, conf, permissions = init_vector

        conf = yaml.safe_load(open(conf))
        abilities = replace_variables(path, conf)

        # iterate through the abilities and replace the commands with the maximum superset.
        # i.e. level=4 -> commands[:4]
        for i, ability in enumerate(abilities):
            permissions = ability['commands']

            # check if the permissions level is set to custom.
            # if true, only the custom commands will be used
            # otherwise, all the commands will add up until the assigned level i.e. 1:4...
            if self.permissions.level == PermissionsLevel.CUSTOM[0]:
                permissions = permissions[self.permissions.level]
            else:
                permissions = permissions[:self.permissions.level]

            abilities[i]['commands'] = permissions

        self.abilities_ = abilities

    def run(self, verbose=True) -> subprocess.CompletedProcess:
        for ability in self.abilities:
            # try to give access to the current payload to be run first
            chmod_args = ['chmod', '+x'] + ability['payloads']
            subprocess.run(chmod_args, capture_output=True)

            # run the payload with the given commands
            output = subprocess.run(ability['payloads'] + ability['commands'], capture_output=True)

            # if you need to debug, add the verbose. This will print in the console the processes.
            # these strings are formatted into bytecode, therefore they should be decoded first.
            if verbose:
                print(
                    output.stdout.decode("utf-8"),
                    TerminalColors.WARNING + output.stderr.decode("utf-8") + TerminalColors.END,
                )

            return output


class Schema:
    """ Generate a list of procedures and tree pathing steps """
    tree: list = []

    def __init__(self, schema: object, attr="id"):
        self.__schema = schema
        self.attr = attr
        self.abilities = self.__schema
        self.weights = self.__schema
        self.flags = self.__schema

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, schema):

        try:
            flags = {category: item["flag"] for category, item in schema.items()}
            self._flags = flags
        except:
            # print("schema does not contain flags")
            pass

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, schema):

        try:
            weights = {technique: val
                       for category, item in schema.items()
                       for technique, val in item["techniques"].items()
                       if type(item) == dict}

            self._weights = weights
        except:
            # print("schema does not contain weights")
            pass

    @property
    def abilities(self):
        return self._abilities

    @abilities.setter
    def abilities(self, schema):
        """
        Set the list of abilities available given the tactics
        tactics_per_category -> list of tuples (ttp category: str, abilities: list of objects)
        """
        tactics_per_category: list = []

        for category, item in schema.items():
            curr_path = os.path.join(TTP, category, "abilities.yml")
            curr_abs = replace_variables(curr_path, {})
            techniques = item["techniques"]

            if techniques != "all":

                if type(techniques) == dict:
                    techniques = techniques.keys()

                curr_abs = list(filter(lambda x: x[self.attr] in techniques, curr_abs))

            if curr_abs:
                tactics_per_category.append((category, curr_abs))

        self._abilities = tactics_per_category

    @staticmethod
    def add_weights(techniques, schema):
        # small mapper function that takes an argument "element" and attempts to find its weight

        def mapper(element):
            # tuple( category, List[abilities_object] )

            def update_weights(li_el):
                if li_el[schema.attr] in schema.weights:
                    li_el["weight"] = schema.weights[li_el[schema.attr]]

                return li_el

            cat, li = element
            li = map(update_weights, li)

            return cat, li

        weighted_abilities = map(mapper, techniques)

        return list(weighted_abilities)


class Parser:
    """ Generic parser to find all kinds of loot information """
    loot: object = {}

    def __init__(self, parser):

        # load the content of the parser plan into the variable
        plan = Parser.load_plan(parser)

        self.mapping = plan['mapping']
        self.flag = plan['flag']
        self.miners: object = plan['miners'] if "miners" in plan else None
        self.target: object = plan['target'] if "target" in plan else None

    def maraud(self, output):
        """ Look for loot based on the given expressions and the pre-defined ones """

        #TODO take a look at the parser
        #output = '\n'.join(output)

        self.loot["ip"] = self.ip(output)
        self.loot["email"] = self.email(output)
        self.loot["filename"] = self.filename(output)

        if self.miners:
            for key, match in self.miners.items():
                self.loot[key] = self.search_match(match, output)

        self.loot["flags"] = self.search_match(self.flag, output)

        targets = self.search_match(self.target, output) if self.target else []

        return targets, self.loot

    @staticmethod
    def load_plan(plan):
        plan_type = type(plan)

        # check if the plan is a path string, and if so, find the file and load the content
        if plan_type == str:
            path = os.path.join(BASE_DIR, "tools", "parsers", plan)

            with open(path) as data:
                return yaml.safe_load(data)

        elif plan_type == object:
            return plan

        else:
            raise TypeError

    @staticmethod
    def search_match(match, blob):
        try:
            group = re.findall(match, blob)
            return list(set(group))
        except Exception as e:
            print(e)

    def ip(self, blob):
        regex = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        return self.search_match(regex, blob)

    def email(self, blob):
        regex = r'[\w.-]+@[\w.-]+'
        return self.search_match(regex, blob)

    def filename(self, blob):
        regex = r'\b\w+\.\w+'
        return self.search_match(regex, blob)
