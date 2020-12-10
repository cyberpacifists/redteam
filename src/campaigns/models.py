"""
Here we will include the decision trees, define how does it work, and the mental process
Each step of the cyber kill chain needs to have a few options itself:

    - goal to reach for the entire node
    - callbacks, to preserve information from each leaf
    - ...

Each node is represented by a worker, which will take an artifact from each ttp category, use tactics as sub-nodes,
and finally use the techniques as leaves:

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
import os
import re
import subprocess
import uuid

from typing import List

from src.tools.models import Schema, Parser, PermissionsLevel
from src.tools.settings import BASE_DIR


class TechniqueNode:
    output: list = []
    __burn: bool = False  # use this variable to know if the technique has been used already.

    def __init__(self, technique: object, level):
        # private vars
        self.__technique = technique

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
    techniques: List[TechniqueNode] = []  # techniques the tactic knows.

    def __init__(self, name):
        # load the tactic from the yaml file passed to it
        self.name = name

    def add_technique(self, technique: TechniqueNode):
        self.techniques.append(technique)

    def get_techniques(self):
        def order_techniques(techniques: List[TechniqueNode]):
            # return the list of techniques in descending order based on the weight of the technique
            return sorted(techniques, key=lambda x: x.weight, reverse=True)

        ordered_ = order_techniques(self.techniques)

        return self.name, ordered_

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TacticNode):
            return NotImplemented
        return self.name == other.name


class ArtifactNode:
    tactics: List[TacticNode] = []  # tactics the artifact has access to.

    def __init__(self, name):
        self.name = name

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
        techniques = [technique for tactic in self.tactics for technique in tactic.techniques]
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
        self.id = uuid.uuid4()
        self.target = target
        self.technique = technique
        self.loot = loot
        self.callback = cb
        self.payload = os.path.join(BASE_DIR, "tools", "payloads", self.technique.payload)

        # include the target into the loot if there isn't yet
        if not self.loot.target:
            self.loot.target = self.target

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

        regex = "\#{(\w+)}.*?"
        pattern = re.compile(regex)

        for i, el in enumerate(args):
            match = pattern.findall(el)

            for group in match:
                # lower case the group and replace the string with the value from the item in the string.
                replacement = getattr(loot, group.lower())
                el = el.replace(
                    f'#{{{group}}}', replacement
                )

            args[i] = el
        return args

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

    def grant_payload_access(self):
        # try to give access to the current payload to be run first
        # in case this does not work, try with 744 mode
        chmod_args = ['chmod', '+x', self.payload]
        subprocess.run(chmod_args, capture_output=True)

    def run(self):

        commands = self._build_arguments(
            commands=self.technique.commands_,
            options=self.technique.options
        )

        commands = self._map_commands(commands, self.loot)

        # run the payload with the given commands
        process = subprocess.Popen(
            [self.payload] + commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        stdout = process.communicate()[0]

        """
        # NOTE: This works best with metasploit
        stdout = []
        stderr = []

        print(f"[!] Worker for {self.technique.name} running... {commands}")

        while process.poll() is None:
            output = process.stdout.readline()

            if output != "":
                stdout.append(output)
                print(output)

            err = process.stderr.readline()
            if err != "":
                stderr.append(err)
                print(err)

        print(f"[!] Worker for {self.technique.name} finished")
        """

        # get the loot gathered by the technique after running.
        targets, loot = self.technique.use(stdout)

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

    def __init__(self, target, port=None, treasure_cb=None):
        self.target = target  # this should be an IP, service or a container name
        self.port = port
        self._treasure_cb = treasure_cb

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

    def flag(self):
        self.flagged = True

    def collect(self, attr):
        try:
            return getattr(self, attr)
        except:
            return self.__loot.get(attr)

    def add_to_loot(self, **kwargs):
        # attempt to include the newly found loot into the loot itself
        for k, val in kwargs.items():
            if type(val) != list:
                val = [val]

            if k in self.__loot:
                self.__loot[k] += val
            else:
                self.__loot[k] = val

    def get_loot(self):
        return self.__loot

    def is_potential_target(self, **kwargs):
        """ run a comparison between the content of the loot to the given arguments """
        for k, val in kwargs.items():
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
                loot = Loot(target.get("target"), target.get("port"))
                # add the extra information in regards to it
                if "extra" in target:
                    loot.add_to_loot(**target["extra"])
                self.add_loot(loot)
            except:
                pass


class Campaign:
    """
    Campaigns are just meant to declare an abstract structure of how and which TTP categories will be used for a
    specific scenario.
    That is, a campaign is meant to set up the scenario and the limitations.
    """
    __nodes: List[ArtifactNode] = []
    __built: bool = False

    def __init__(self, plan):
        self.plan_ = plan

    @property
    def plan_(self):
        return self._plan

    @plan_.setter
    def plan_(self, plan):
        self._plan = plan
        self.preconditions = plan["preconditions"]
        self.schema = Schema(plan["schema"])
        self.flags = self.schema.flags


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
    local_network: str = "192.168.0.0/24"

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
            pre_loot = Loot(target=Logic.local_network, treasure_cb=treasure.scatter)

        treasure.add_loot(pre_loot)
        return treasure

    @staticmethod
    def treasure_hunter(tree, flags, preconditions: dict = None, iterations: int = 1):

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

            while iterations > 0 and not success:
                # reduce the number of iterations left
                iterations -= 1

                # iterate through the techniques, and run them with the targets.
                # remember the techniques are sorted by weight, therefore the "heavier" ones will run first!
                for technique in techniques:
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
                                print(f"[SUCCESS] category: {node.name} > technique: {technique.name} > target: {loot.target}")
                                break
