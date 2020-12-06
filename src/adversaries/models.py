"""
These adversaries are meant to add another level of interaction with the blue team.

Generally, adversaries can be classified by their motive and the way they do things.
To be more precise, adversaries use different schemas and techniques depending on their purpose.

Let's say, a hack-activist will follow different paths and use different methods to a burglar, and that one from
a government employee.

These classes will define how they interact with the systems, how destructive they are, how intrusive, which tools
they will use, and so on.
"""
from src.tools.models import Schema
from src.campaigns.models import Campaign


class Adversary:
    """
    This class is the top level adversary, the decisions maker, the way the app behaves
    """
    __campaign: Campaign = None

    def __init__(self, profile, networks=None):
        self.profile = profile

        # initialization vector for the networks available to this adversary.
        self.networks = networks

    @property
    def networks(self):
        return self.networks_

    @networks.setter
    def networks(self, network_addresses):
        # initialize the networks to the given addresses.
        networks = []

        if network_addresses:
            for network in network_addresses:
                n_ = Network(network)
                networks.append(n_)

        self.networks_ = networks

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile_object: object):
        profile = profile_object["profile"]
        self._profile = profile

        self.logic = profile["logic"]
        self.schema = Schema(profile["schema"])

    def build_adversary(self, campaign: Campaign):
        """
        This function will create a logical decision tree based on the characteristics already given to him.

        To create this decision tree, we help ourselves with the kill-chain, to stipulate the mental process that
        the attacker must follow, and the TTPs categories
        """
        tree = campaign.get_adversary_tree(self.schema)  # this is a tree
        logic = self.get_logic()  # this is a function # self.logic

        return tree, logic

    def get_logic(self):
        return getattr(Logic, self.logic)


class Logic:
    @staticmethod
    def simple(tree, it: int = 5):
        node_targets: list = []
        node_loot: object = {}

        def run_node(node, iterations, loot=None, targets: list = None):
            # add the loot to the node
            if loot:
                node.add_loot(loot)
            # add the list of targets to the node
            if targets:
                node.targets = targets

            # sub-nodes, containing the tactic name and the techniques
            techniques = [tactic.get_techniques() for tactic in node.tactics]

            # use each technique once in the given order
            for tactic, technique_list in techniques:
                for technique in technique_list:
                    # TODO perhaps send this to the worker
                    technique._run()

            # return the loot if succeeded, or if it got to the iterations limit
            if node.success or iterations == 0:
                return node.get_loot()
            else:
                return run_node(node, iterations - 1)

        for tree_node in tree:
            l_ = run_node(tree_node, iterations=it, loot=node_loot, targets=node_targets)
            if "targets" in l_:
                node_targets = l_["targets"]

            node_loot.update(l_)


class Network:
    """
    Define the network and the characteristics of it
    """
    hosts: set = set()

    def __init__(self, network_address):
        self.network_address = network_address

    def add_new_host(self, ip_address, mac_address=None, ports=None, fingerprint=None, update=False):
        # Declare the new host to be introduced and evaluated
        h_ = Host(ip_address=ip_address, mac_address=mac_address)
        h_.ports = ports
        h_.fingerprint = fingerprint

        if h_ in self.hosts:
            sentence = f'[-] Host with ip "{ip_address}"' + f'{f"and mac {mac_address}" if mac_address else ""}'\
             + " already in the host list"

            print(sentence)

            if update:
                self.hosts.remove(h_)
                self.hosts.add(h_)

        else:
            self.hosts.add(h_)


class Fingerprint:
    vulnerabilities: list = []  # list of known vulnerabilities for this system

    def __init__(self, process_name: str, version: str):
        self.name: str = process_name  # System/process name
        self.version: str = version


class Host:
    """ Define a host target and its characteristics """
    ports: list = []  # list of open/filtered ports
    infected: bool = False  # define whether the host has been infected by the adversary or not
    rooted: bool = False  # define if the host has been rooted i.e. we have the root user for the machine
    fingerprint: Fingerprint = None  # a fingerprint object containing relative host information

    def __init__(self, ip_address, mac_address=None):
        self.ip = ip_address
        self.mac = mac_address

        # list of users in the host. This property needs to be initialized with the class.
        self.users: list = []

    def __hash__(self):
        return hash((self.ip, self.mac))

    def __eq__(self, other) -> object:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.ip == other.ip and self.mac == other.mac

    @property
    def users(self):
        return self._users

    @users.setter
    def users(self, user_list):
        if user_list:
            self._users = [User(user) for user in user_list]


class Port:
    """
    This class contains information in regards to a Port
    """
    fingerprint: Fingerprint = None  # a fingerprint object containing relative process information

    def __init__(self, port_number: int):
        pass


class User:
    """
    Every Host will have a list of users. These users will have different privileges and access levels.
    """
    root: bool = False  # We assume the user won't be the root user initially

    def __init__(self, username, password=None, privileges=None):
        self.username = username
        self.password = password

        # set of privileges linked to the user
        self.privileges: set = privileges
