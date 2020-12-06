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
import subprocess

from typing import List

from src.tools.models import Schema, TerminalColors
from src.tools.settings import TTP


class TechniqueNode:
    parser = None
    output: list = []
    __burn: bool = False  # use this variable to know if the technique has been used already.

    def __init__(self, technique: object, callbacks):
        # private vars
        self.__technique = technique
        self.__callbacks = callbacks

        # TODO implement the weights into the techniques
        self.weight = 100

        # attrs
        self.name = technique['technique']
        self.commands = technique['commands']
        self.payload = technique['payload']
        self.options = technique['options']

    def __str__(self):
        return self.name

    def __notify(self, loot):
        callback = self.__callbacks["notify"]
        callback(loot)

    def _run(self):
        callback = self.__callbacks["run"]
        callback(self, verbose=True)

    # Public method to use the technique
    def use(self, output):
        self.burn()

        # if there is a parser in place, parse the output to collect the loot
        if self.parser:
            loot = self.parser(output)
            # Notify the artifact of the loot collected during the run
            self.__notify(loot)

        # include the current output, without parsing, into the techniques output record
        from datetime import datetime
        self.output.append((datetime.now(), output))

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
            # TODO add weights to the TechniqueNode
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
    __loot: object = {}  # contains relevant information related to the artifact leaf nodes.

    tactics: List[TacticNode] = []  # tactics the artifact has access to.
    targets: list = []
    success: bool = False  # whether this artifact is done or not with a successful result

    def __init__(self, name, flag: hash):
        self.name = name
        self.path = os.path.join(TTP, name)
        self.flag = flag  # hash of the objective

    def add_tactic(self, tactic: TacticNode):
        self.tactics.append(tactic)

    def get_technique(self, name):

        # find the technique given the name
        for tactic in self.tactics:
            techniques = tactic.techniques
            for technique in techniques:
                if str(technique) == name:
                    return technique

    def run_technique(self, technique, verbose: bool = False):

        # check if the technique given is a string or
        technique_type = type(technique)
        if technique_type == str:
            technique = self.get_technique(technique)
        elif technique_type is not TechniqueNode:
            raise TypeError("Type of technique not accepted")

        def build_arguments(**kwargs):
            args = []
            for arg in kwargs.values():
                arg = filter(lambda x: x is not None, arg)
                if arg:
                    args += arg

            return args

        # find the payloads
        payload = [os.path.join(self.path, technique.payload)]

        # combination of arguments, commands, options and targets.
        arguments = build_arguments(commands=technique.commands, options=technique.options, targets=self.targets)

        # try to give access to the current payload to be run first
        # in case this does not work, try with 744 mode
        chmod_args = ['chmod', '+x'] + payload
        subprocess.run(chmod_args, capture_output=True)

        # run the payload with the given commands
        output = subprocess.run(payload + arguments, capture_output=True)

        # if you need to debug, add the verbose. This will print in the console the processes.
        # these strings are formatted into bytecode, therefore they should be decoded first.
        if verbose:
            print(
                output.stdout.decode("utf-8"),
                TerminalColors.WARNING + output.stderr.decode("utf-8") + TerminalColors.END,
            )

        # burns the technique so it is marked as used
        technique.use(output)

        return output

    def add_loot(self, loot):
        self.__loot.update(loot)

        # compare the loot to the flag
        self.check_flag(loot)

    def get_loot(self):
        return self.__loot

    def check_flag(self, flag):
        # compare the flag passed to the flag set for the artifact
        check = hash(flag) == self.flag

        if check:
            self.success = True

        return check

    def set_targets(self, targets: list):
        self.targets = targets

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, ArtifactNode):
            return NotImplemented
        return self.name == other.name


class Campaign:
    """
    Campaigns are just meant to declare an abstract structure of how and which TTP categories will be used for a
    specific scenario.
    That is, a campaign is meant to set up the scenario and the limitations.
    """
    __nodes: List[ArtifactNode] = []
    __built: bool = False

    def __init__(self, schema: Schema, flags: object):
        self.__schema = schema
        self.abilities = schema.abilities
        self.flags: object = flags

    def get_abilities_intersection(self, abilities):

        ttp = []
        s_ab = dict(self.__schema.abilities)

        for ability in abilities:
            _ = []
            cat, cat_abs = ability

            if cat in s_ab.keys():
                abs_list = [x for x in s_ab[cat] if x in cat_abs]
                ttp.append((cat, abs_list))

        return ttp

    def get_adversary_tree(self, adversary_schema: Schema):
        """ Based on an adversary schema, build the tree """

        # get the intersection between the campaign abilities and the adversary abilities, and rebuild the tree.
        self.abilities = self.get_abilities_intersection(adversary_schema.abilities)
        tree = self.build(abilities=self.abilities)

        return tree

    def get_tree(self):
        if self.__built:
            return self.__nodes

    def build(self, flags: object = None, abilities=None):
        """ Build the nodes tree based on the given abilities """
        def sort_abilities(abs_list):
            """ Sort the techniques from the abilities object """
            t_ = {}

            for ab in abs_list:
                cur_tac = ab['tactic']
                if cur_tac in t_:
                    t_[cur_tac].append(ab)
                else:
                    t_[cur_tac] = [ab]

            return t_

        nodes = []
        flags = flags if flags else self.flags
        abilities = abilities if abilities else self.abilities

        # create and append all the nodes to the tree list.
        for node in abilities:
            # each node in the schema is divided into the category and the abilities in it.
            category, abilities = node
            flag = flags[category]

            category = ArtifactNode(category, flag)
            tactics = sort_abilities(abilities)
            callbacks = {
                "run": category.run_technique,
                "notify": category.add_loot
            }

            # create a tactic node and iterate through the techniques
            for tactic, techniques in tactics.items():
                tactic = TacticNode(tactic)

                # create technique nodes and add them to the tactic
                for technique in techniques:
                    tactic.add_technique(TechniqueNode(technique, callbacks))

                category.add_tactic(tactic)

            nodes.append(category)

        self.__built = True
        self.__nodes = nodes

        return self.__nodes
