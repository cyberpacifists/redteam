import re
import subprocess
import yaml
import random
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
    RANDOM = random.randint(0, 5), 'random'


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
        with open(path) as yaml_data:
            return yaml.load(yaml_data, Loader=loader)


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
            permissions = abilities[i]['commands']

            # check if the permissions level is set to custom.
            # if true, only the custom commands will be used
            # otherwise, all the commands will add up until the assigned level i.e. 1:4...
            if self.permissions.level == PermissionsLevel.CUSTOM[0]:
                permissions = permissions[self.permissions.level]
            else:
                permissions = permissions[:self.permissions.level]

            abilities[i]['commands'] = permissions

        self.abilities_ = abilities

    def run(self, verbose=False) -> subprocess.CompletedProcess:
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
