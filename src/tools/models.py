"""
    Worker:
    +--------------------------+
    |        Artifact          |
    |           |              |
    |      -----------         |
    |     |          |         |
    |   tactic     tactic      |
    |     |          |         |
    |  ------     ------       |
    | |     |     |     |      |
    | tec  tec   tec   tec     |
    +--------------------------+
"""

import re
import subprocess
import yaml
import random
import json
import time

from .settings import *
from typing import List
from datetime import datetime


class TerminalColors:
    OK = '\u001b[32m'
    WARNING = '\033[93m'
    END = '\033[0m'

    @staticmethod
    def block(string):
        print(f"\u001b[48;1;41m{string}{TerminalColors.END}")

    @staticmethod
    def rainbow(string):
        t = ''.join([f'\u001b[3{i}m{s}{TerminalColors.END}' for i, s in enumerate(string)])
        print(t)


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

    def __init__(self, target, level=PermissionsLevel.NOOB, abilities_path='abilities.yml', conf_path=''):
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

    def __init__(self, schema: object, attr="id"):
        self.__schema = schema
        self.attr = attr
        self.abilities = self.__schema
        self.weights = self.__schema
        self.flags = self.__schema
        self.tree: list = []

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

    def __init__(self, parser):

        # load the content of the parser plan into the variable
        plan = Parser.load_plan(parser)

        self.flag = plan['flag']
        self.miners = plan['miners'] if "miners" in plan else None
        self.target: dict = plan['target'] if "target" in plan else None
        self.loot: object = {}

        # Other non implemented features
        # self.mapping: dict = plan['mapping'] if "mapping" in plan else None

    def maraud(self, output):
        """ Look for loot based on the given expressions and the pre-defined ones """
        self.loot["flags"] = self.search_match(self.flag, output)

        self.loot["ip"] = self.ip(output)
        self.loot["email"] = self.email(output)
        self.loot["filename"] = self.filename(output)

        if self.miners:
            if type(self.miners) == str:
                # if the miner is a string, that means that it is a pattern with named groups
                miners = self.named_search(self.miners, output)

                # combine the current state of the loot with all the values found from the miners
                for miner in miners:
                    for key, match in miner.items():
                        self.loot[key] = self.loot[key] + [match] if key in self.loot else [match]

            else:
                # we understand that the miner could be either a string or a dictionary
                for key, match in self.miners.items():
                    self.loot[key] = self.search_match(match, output)

        # targets = self.search_match(self.target, output) if self.target else []
        targets = []
        if self.target:
            if "<" in self.target and ">" in self.target:
                targets = self.named_search(self.target, output)

        return targets, self.loot

    @staticmethod
    def load_plan(plan):
        plan_type = type(plan)

        # check if the plan is a path string, and if so, find the file and load the content
        if plan_type == str:
            path = os.path.join(BASE_DIR, "tools", "parsers", plan)

            with open(path) as data:
                return yaml.safe_load(data)

        elif plan_type == dict:
            return plan

        else:
            raise TypeError

    @staticmethod
    def named_search(match, blob) -> list:
        try:
            matches = re.finditer(match, blob, re.MULTILINE)
            return [match.groupdict() for match in matches]

        except Exception as e:
            print(e)

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


class TechniqueNode:

    def __init__(self, technique: object, level):
        # private vars
        self.__technique = technique
        self.__burn: bool = False  # use this variable to know if the technique has been used already.

        self.output: list = []
        self.level, self.skill_level = level

        # required attrs
        # TODO load this as a dictionary of **kwargs
        self.name = technique['name']
        self.technique = technique['technique']
        self.commands_ = technique['commands']  # commands is a python keyword, careful!
        self.payload = technique['payload']
        self.parser = technique['parser']

        # optional attrs
        self.options = technique['options'] if 'options' in technique else []
        self.weight = technique['weight'] if 'weight' in technique else 100
        self.requires = technique['requires'] if "requires" in technique else {}  # list of loot requirements
        self.timeout = technique['timeout'] if "timeout" in technique else None

    @property
    def commands_(self):
        return self._commands

    @commands_.setter
    def commands_(self, commands):
        # based on the permissions level, define the number of commands allowed for the adversary to run on his
        # behalf. Whereas the commands will stack until the given level, or use the custom command if so.
        if self.level < PermissionsLevel.CUSTOM[0]:
            commands = commands[:self.level]
        elif self.level == PermissionsLevel.CUSTOM[0]:
            commands = commands[self.level]

        self._commands = commands

    @property
    def parser(self):
        return self._parser

    @parser.setter
    def parser(self, parser_plan_path):
        if parser_plan_path:
            self._parser = Parser(parser_plan_path)

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TechniqueNode):
            return NotImplemented
        return self.name == other.name

    # Public method to use the technique
    def use(self, output):
        self.burn()

        # include the current output, without parsing, into the techniques output record
        from datetime import datetime
        self.output.append((datetime.now(), output))

        # if there is a parser in place, parse the output to collect the loot
        if self.parser:
            loot = self.parser.maraud(output)
            return loot

    def is_burnt(self):
        return self.__burn

    def burn(self):
        self.__burn: bool = True


class TacticNode:

    def __init__(self, name):
        # load the tactic from the yaml file passed to it
        self.name = name
        self.techniques: List[TechniqueNode] = []  # techniques the tactic knows.

    def add_technique(self, technique: TechniqueNode):
        self.techniques.append(technique)

    def get_techniques(self):
        def order_techniques(techniques: List[TechniqueNode]):
            # return the list of techniques in descending order based on the weight of the technique
            return sorted(techniques, key=lambda x: x.weight, reverse=True)

        ordered_ = order_techniques(self.techniques)

        return ordered_

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TacticNode):
            return NotImplemented
        return self.name == other.name


class ArtifactNode:
    def __init__(self, name):
        self.name = name
        self.tactics: List[TacticNode] = []  # tactics the artifact has access to.

    def add_tactic(self, tactic: TacticNode):
        self.tactics.append(tactic)

    def get_technique(self, name):
        # find the technique given the name
        for tactic in self.tactics:
            techniques = tactic.techniques
            for technique in techniques:
                if str(technique) == name:
                    return technique

    def get_all_techniques(self):
        techniques = [technique for tactic in self.tactics for technique in tactic.get_techniques()]
        return techniques

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, ArtifactNode):
            return NotImplemented
        return self.name == other.name


class Worker:
    """ This class is meant to run techniques """

    def __init__(self, target, technique, loot, cb):
        self.target = target
        self.technique = technique
        self.loot = loot
        self.callback = cb
        self.payload = os.path.join(BASE_DIR, "tools", "payloads", self.technique.payload)

        self.log = datetime.now().strftime('%d-%b-%Y')

        # include the target into the loot if there isn't yet
        if not self.loot.target:
            self.loot.target = self.target

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, filename):
        filename = os.path.join(BASE_DIR, "tools", "logs", filename + '.log')
        self._log = open(filename, 'a+')

    @property
    def technique(self):
        return self._technique

    @technique.setter
    def technique(self, technique):
        technique_type = type(technique)
        if technique_type == str:
            technique = self.callback(technique)
        elif technique_type is not TechniqueNode:
            raise TypeError("Type of technique not accepted")

        self._technique = technique

    @staticmethod
    def _build_arguments(**kwargs) -> list:
        """ remove empty, None arguments """
        args = []
        for arg in kwargs.values():
            arg = filter(lambda x: x is not None, arg)
            if arg:
                args += arg

        return args

    @staticmethod
    def _map_commands(args: list, loot):
        """
        Find the variables in the commands, and replace them with the attributes from the loot.
        Typically, this will only represent TARGET and PORT
        """
        regex = "\#{(\w+)}.*?"
        pattern = re.compile(regex)

        for i, el in enumerate(args):
            match = pattern.findall(el)

            for group in match:
                # lower case the group and replace the string with the value from the item in the string.
                replacement = loot.collect(group.lower())

                # TODO quick fix to include the session in the loot
                if type(replacement) == list:
                    replacement = replacement[0]

                el = el.replace(
                    f'#{{{group}}}', replacement
                )

            args[i] = el
        return args

    @staticmethod
    def capture(process, live: bool = False):

        stdout = ""
        stderr = ""

        if live:
            # NOTE: This works best with metasploit (!!!)
            while not process.poll():
                output = process.stdout.readline()
                if output != "":
                    stdout += output
                    print(output)

                err = process.stderr.readline()
                if err != "":
                    stderr += err
                    print(err)
        else:
            stdout, stderr = process.communicate()

        return stdout, stderr

    def write(self, stdout, commands, loot=None, stderr=None, verbose=True,
              log_errs: bool = False,
              log_loot: bool = False):

        # declare at which time this worker was run
        date_now = f"{datetime.now()}\n"

        # log file linting
        info = "info"
        err = "error "
        warning = "w "

        # starting and ending messages
        start = f"{info} Worker for {self.technique.name} running... {commands}\n"
        end = f"\n{info} Worker for {self.technique.name} finished\n"

        data = date_now + start + stdout
        if stderr and log_errs:
            data += err + stderr

        if loot and log_loot:
            data += warning + json.dumps(loot, indent=2)

        # add the ending to the data
        data = data + end

        # write this to the file
        self.log.write(data)

        if verbose:
            print(data)

    def grant_payload_access(self):
        # try to give access to the current payload to be run first
        # in case this does not work, try with 744 mode
        chmod_args = ['chmod', '+x', self.payload]
        subprocess.run(chmod_args, capture_output=True)

    def run(self):
        """
        Runs a technique in a separated subprocess, grab the output, parse it, generate loot and
        potentially generate new targets
        """
        commands = self._build_arguments(
            commands=self.technique.commands_,
            options=self.technique.options,
        )

        commands = self._map_commands(commands, self.loot)

        # run the payload with the given commands
        process = subprocess.Popen(
            [self.payload] + commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Use communicate to avoid deadlocks on the pipe buffer
        stdout, stderr = self.capture(process)

        # get the loot gathered by the technique after running.
        targets, loot = self.technique.use(stdout)

        # write the output to the log file
        self.write(stdout, commands, loot=loot, stderr=stderr, verbose=True)

        # update the current loot bag with the data found in it
        self.loot.add_to_loot(**loot)

        return targets


class Loot:
    """ This class is meant to define the loot gathered from the technique used """

    # make this private and only accessible by the class itself, so we cannot temper with it
    __loot = {
        "ip": [],
        "email": [],
        "filename": [],
        "port": [],
        "target": [],
        "flags": []
    }

    flagged: bool = False

    def __init__(self, target, port=None, session=None, treasure_cb=None):
        self.target = target  # this should be an IP, service or a container name
        self.port = port
        self.session = session
        self._treasure_cb = treasure_cb

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, s):
        self.add_to_loot(session=s)
        self._session = s

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, t):
        self.add_to_loot(ip=t)
        self._target = t

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, p):
        if p:
            self.add_to_loot(port=p)
            self._port = p

    def update(self, target, port, session, **kwargs):
        self.target = target
        self.port = port
        self.session = session

        self.add_to_loot(**kwargs)

    def flag(self):
        self.flagged = True

    def collect(self, attr):
        try:
            item = getattr(self, attr)

            # check if the attribute does have any value
            if item is not None:
                return item
            else:
                return self.__loot.get(attr)

        except:
            return self.__loot.get(attr)

    def add_to_loot(self, **kwargs):
        # attempt to include the newly found loot into the loot itself
        for k, val in kwargs.items():
            if val and val is not None:
                if type(val) != list:
                    val = [val]

                if k in self.__loot:
                    self.__loot[k] += val
                else:
                    self.__loot[k] = val

                self.__loot[k] = list(set(self.__loot[k]))

    def get_loot(self):
        return self.__loot

    def is_potential_target(self, **kwargs):
        """ run a comparison between the content of the loot to the given arguments """

        for k, val in kwargs.items():
            if k not in self.__loot:
                return False
            if val:
                val = str(val)
                # it might be the case that there is no value at all, which will be considered then as "any"
                if val not in self.__loot[k]:
                    return False
        return True

    def scatter_treasure(self, attr):
        """
        NOTE: not implemented!
        This is meant to investigate the treasure in which this loot is for a specific item, i.e. all the IP's logged.
        """
        if self._treasure_cb:
            return self._treasure_cb(attr)


class Treasure:
    """ Collect all the loot from the whole scenario here"""

    def __init__(self, loot: Loot = None):
        self.loot = loot

    @property
    def loot(self):
        return self._loot

    @loot.setter
    def loot(self, l_):
        self._loot = [l_] if l_ else []

    def count(self):
        return len(self._loot)

    def add_loot(self, loot: Loot):
        self.loot.append(loot)

    def scatter(self, attr):
        """ returns a flat array containing all the elements inside each loot item """
        return [e for loot in self.loot for e in loot.collect(attr)]

    def find_potential_target(self, req):
        return [loot for loot in self.loot if loot.is_potential_target(**req)]

    def create_loot(self, target_list: List[dict]):
        # create a new loot bags from the objects given
        # the list will contain information relevant to each target
        for target in target_list:
            try:
                # create the new loot bag
                loot = list(filter(lambda x: x.target == target.get("target"), self.loot))
                if loot:
                    loot[0].update(**target)
                else:
                    loot = Loot(target.get("target"), port=target.get("port"))
                    loot.add_to_loot(**target)
                    self.add_loot(loot)
            except:
                pass


class AdversaryTree:
    """ A tree containing the nodes and leaves """
    _nodes: List[ArtifactNode] = []

    def __init__(
            self,
            campaign_schema: Schema,
            adversary_schema: Schema,
            level=PermissionsLevel.NOOB,
            auto: bool = True):

        self.c_schema = campaign_schema
        self.a_schema = adversary_schema
        self.level = level

        if auto:
            # load the intersection of abilities between the campaign and the adversary
            abilities = self.get_abilities_intersection(
                self.c_schema.abilities,
                self.a_schema.abilities
            )

            # add the weights to the abilities from the adversary schema
            abilities = Schema.add_weights(abilities, self.a_schema)

            # build the tree
            self.build(abilities, level)

    def get_tree(self):
        return self._nodes

    @staticmethod
    def get_abilities_intersection(c_abilities, a_abilities):
        abilities = []

        c_abilities = dict(c_abilities)
        a_abilities = dict(a_abilities)

        for c_category, c_category_abilities in c_abilities.items():
            # TODO there is a bug in the tree which makes the nodes duplicate

            if c_category in a_abilities.keys():
                intersection = [x for x in a_abilities[c_category] if x in c_category_abilities]
                abilities.append((c_category, intersection))

        return abilities

    def build(self, abilities, level):
        def sort_abilities(abs_list):
            """ Sort the techniques from the abilities object """
            tac_ = {}

            for ab in abs_list:
                cur_tac = ab['tactic']
                if cur_tac in tac_:
                    tac_[cur_tac].append(ab)
                else:
                    tac_[cur_tac] = [ab]
            return tac_

        nodes = []

        for node in abilities:
            # each node in the schema is divided into the category and the abilities in it.
            category, abilities = node

            category = ArtifactNode(category)
            tactics = sort_abilities(abilities)

            # create a tactic node and iterate through the techniques
            for tactic, techniques in tactics.items():
                tactic = TacticNode(tactic)

                # create technique nodes and add them to the tactic
                for technique in techniques:
                    t_ = TechniqueNode(technique=technique, level=level)
                    tactic.add_technique(t_)

                category.add_tactic(tactic)

            nodes.append(category)

        self._nodes = nodes
        return self._nodes


class Logic:
    defenders_network: str = DEFENDERS_NETWORK

    @staticmethod
    def build_preconditions_treasure(preconditions: dict = None):
        # create a treasure which will be shared through the whole logic and initialize it with some
        # loot from the scenario or local network loot!
        treasure = Treasure()

        if preconditions:
            # if there is a preconditions object, create some loot around it
            pre_target = preconditions.get("target")
            pre_port = preconditions.get("port")
            extra = preconditions.get("extra")

            pre_loot = Loot(target=pre_target, port=pre_port, treasure_cb=treasure.scatter)

            if extra:
                pre_loot.add_to_loot(**extra)
        else:
            pre_loot = Loot(target=Logic.defenders_network, treasure_cb=treasure.scatter)

        treasure.add_loot(pre_loot)
        return treasure

    @staticmethod
    def treasure_hunter(tree, flags, preconditions: dict = None, iterations_allowed: int = 1):

        # build the treasure
        treasure = Logic.build_preconditions_treasure(preconditions)

        # iterate through the nodes in vertical fashion
        for node in tree:
            # initialize the flag and set the success of the node to False, so we can start running techniques
            # until the flag is found
            success: bool = False
            flag = flags.get(node.name)

            # collect all the techniques available in one simple array
            techniques = node.get_all_techniques()
            iterations = iterations_allowed

            print(f"{TerminalColors.OK}Category: {node.name} {TerminalColors.END}")

            while iterations > 0 and not success:
                # reduce the number of iterations left
                iterations -= 1

                # iterate through the techniques, and run them with the targets.
                # remember the techniques are sorted by weight, therefore the "heavier" ones will run first!
                for technique in techniques:
                    # for debugging purposes, print the current status.
                    print(
                        TerminalColors.WARNING + str(technique) + "\n",
                        f"Loot: {treasure.count()}" + TerminalColors.END)

                    loots = treasure.find_potential_target(technique.requires)

                    # iterate through the loot and run the technique as many times as potential loot allows
                    for loot in loots:
                        # running a worker will make use of the technique and burn it
                        # it will also generate new loot, which should be added to the treasure
                        worker = Worker(
                            technique=technique,
                            target=loot.target,
                            loot=loot,
                            cb=node.get_technique
                        )

                        new_targets = worker.run()

                        treasure.create_loot(new_targets)

                        # once the worker is done, check the flags gathered in the loot,
                        # play them against the current flag, and mark the loot box as a good one.
                        for loot_flag in loot.collect("flags"):

                            if flag == loot_flag:
                                success = True
                                TerminalColors.block(f"[SUCCESS] category: {node.name} "
                                                     f"> technique: {technique.name} "
                                                     f"> target: {loot.target}"
                                                     )

                                EVENT_DISPATCHER.send(
                                    signal='redteam-flags',
                                    sender=__name__,
                                    event={
                                        'category': node.name,
                                        'technique': technique.name,
                                        'target': loot.target,
                                        'flag_status': 'captured',
                                    }
                                )

                                break
            print(f"Waiting {TURN_SLEEP} seconds until next action...")
            time.sleep(TURN_SLEEP)
        TerminalColors.rainbow("Game Done")
