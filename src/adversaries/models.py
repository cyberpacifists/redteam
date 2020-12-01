"""
These adversaries are meant to add another level of interaction with the blue team.

Generally, adversaries can be classified by their motive and the way they do things.
To be more precise, adversaries use different schemas and techniques depending on their purpose.

Let's say, a hack-activist will follow different paths and use different methods to a burglar, and that one from
a government employee.

These classes will define how they interact with the systems, how destructive they are, how intrusive, which tools
they will use, and so on.
"""

from src.tools.settings import *
import yaml


class Adversary:
    """
    This class is the top level adversary, the decisions maker, the way the app behaves
    """

    def __init__(self, profile, schema, objective, abilities, networks=None):
        self.profile = profile
        self.objective = objective
        self.abilities = abilities
        self.schema = schema

        # initialization vector for the networks available to this adversary
        self.networks = networks

    def build_adversary(self):
        """
        This function will create a logical decision tree based on the characteristics already given to him.

        To create this decision tree, we help ourselves with the kill-chain, to stipulate the mental process that
        the attacker must follow, and the TTPs categories
        """
        pass

    @property
    def networks(self):
        return self.networks_

    @networks.setter
    def networks(self, network_addresses):
        # initialize the networks to the given addresses.
        networks = []

        for network in network_addresses:
            n_ = Network(network)
            networks.append(n_)

        self.networks_ = networks


class Schema:
    """
    Generate a list of procedures and tree pathing steps
    """

    def __init__(self, tactics: list):
        # get the list of abilities from a list of tactics given list of string tactics
        self.abilities = tactics

    @property
    def abilities(self):
        return self.abilities_

    @abilities.setter
    def abilities(self, tactics):
        tactics_per_category = []

        # transverse the whole ttp path to get the list of abilities defined.
        for root, dirs, files in os.walk(TTP, topdown=False):
            for dir_i in dirs:
                # identify if the current abilities path exists
                curr_abs_path = os.path.join(os.path.join(TTP, dir_i), 'abilities.yml')

                if os.path.exists(curr_abs_path):

                    # open the abilities file and filter it to get the set of given abilities
                    curr_abs = yaml.safe_load(open(curr_abs_path))
                    curr_abs = filter(lambda x: x['tactic'] in tactics, curr_abs)

                    # check if there is still any ability in the array, and if so add it with the category name
                    # to the list
                    if curr_abs:
                        tactics_per_category.append((dir_i, curr_abs))

        self.abilities_ = tactics_per_category


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
    """
    Define a host target and its characteristics
    """
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
        return self.users_

    @users.setter
    def users(self, user_list):
        if user_list:
            self.users_ = [User(user) for user in user_list]


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
