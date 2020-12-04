# -*- coding: utf-8 -*-
"""
Tactics and Techniques module.

This module implements classess for the attack Techniques and their
categories (aka. Tactics).
All Techniques have a "execute" method, typically by implementing
an "Executor" interface (like "MetasploitExecutor" also defined in this
module).

to-do:
- Flags in separate classes
- enum
- fingerprint / vuln scan
- mysql: https://attack.mitre.org/techniques/T1555/
- data destruction https://attack.mitre.org/techniques/T1485/
- wordpress pw brute force https://attack.mitre.org/techniques/T1110/001/
"""

from abc import ABC, abstractmethod # to implement interfaces in python

from .errors import ActionExecutionError


class MetasploitExecutor():
    """Executes an arbitrary Metasploit module"""
    def __init__(self, module_name):
        self.kind = 'msfrpc'
        self.module_name = module_name
    def execute(self, worker, parameters):
        if '_timeout' in parameters:
            timeout = parameters['_timeout']
        else:
            timeout = None
        commands = [
            f'use {self.module_name}'
        ]
        for key, value in parameters.items():
            if not key.startswith('_'):
                commands.append(f'set {key} {value}')
        commands.append('run -z')
        worker.execute('\n'.join(commands), wait=True, timeout=timeout)


class Tactic(ABC): # pylint: disable=too-few-public-methods
    """Abstract class for Tactics"""
    @property
    @abstractmethod
    def tactic_id(self):
        pass
    @property
    @abstractmethod
    def tactic_name(self):
        pass


class DiscoveryTactic(Tactic):
    tactic_id = 'TA0007'
    tactic_name = 'Discovery'


class LateralMovementTactic(Tactic):
    tactic_id = 'TA0008'
    tactic_name = 'Lateral Movement'


class CredentialAccessTactic(Tactic):
    tactic_id = 'TA0006'
    tactic_name = 'Credential Access'


class Technique(ABC):
    """Abstract class for Techniques"""
    @property
    @abstractmethod
    def technique_id(self):
        pass
    @property
    @abstractmethod
    def name(self):
        pass
    @property
    @abstractmethod
    def skill_score(self):
        pass
    @property
    @abstractmethod
    def stealth_score(self):
        pass

    @abstractmethod
    def execute(self, worker, parameters):
        pass


class RemoteSystemDiscoveryTechnique(
    Technique,
    DiscoveryTactic
):
    technique_id = 'T1018'
    name = 'Remote System Discovery'


# class PingNetworkServiceScanningTechnique(
#     MetasploitExecutor,
#     RemoteSystemDiscoveryTechnique
# ):
#     technique_id = 'T1018.401'
#     name = 'Ping Remote System Discovery',
#     skill_score = 5
#     stealth_score = 60
#     module_name = 'post/multi/gather/ping_sweep'
#     def __init__(self):
#         super().__init__(self.module_name)


class NetworkServiceScanningTechnique(
    Technique,
    DiscoveryTactic
):
    technique_id = 'T1046'
    name = 'Network Service Scanning',


class SynNetworkServiceScanningTechnique(
    MetasploitExecutor,
    NetworkServiceScanningTechnique
):
    technique_id = 'T1046.401'
    name = 'SYN Network Service Scanning',
    skill_score = 10
    stealth_score = 60
    module_name = 'auxiliary/scanner/portscan/syn'
    def __init__(self):
        super().__init__(self.module_name)

class NetworkServiceScanningTechnique(
    MetasploitExecutor,
    Technique,
    DiscoveryTactic
):
    technique_id = 'T1046'
    name = 'Network Service Scanning',
    skill_score = 5
    stealth_score = 60
    module_name = 'exploits/unix/webapp/wp_phpmailer_host_header'
    def __init__(self):
        super().__init__(self.module_name)


class ExploitationOfRemoteServicesTechnique(
    MetasploitExecutor,
    Technique,
    LateralMovementTactic
):
    technique_id = 'T1210'
    name = 'Exploitation of Remote Services',
    skill_score = 50
    stealth_score = 50
    module_name = 'exploits/unix/webapp/wp_phpmailer_host_header'
    def __init__(self):
        super().__init__(self.module_name)


class OSCredentialDumpingTechnique(Technique, CredentialAccessTactic):
    technique_id = 'T1003'
    name = 'OS Credential Dumping Technique'


class DumpWordpressConfigTechnique(
    MetasploitExecutor,
    OSCredentialDumpingTechnique
):
    technique_id = 'T1003.401'
    name = 'Dump Wordpress Configuration'
    skill_score = 15
    stealth_score = 95
    module_name = 'post/linux/gather/enum_wordpress'
    def __init__(self):
        super().__init__(self.module_name)


# class ExecuteSessionCommandTechnique(Technique):
#     """Executes an arbitrary command in a session """
#     def __init__(self, command, terminating_string):
#         self.kind = 'msfrpc'
#         self.command = command
#         # self.terminating_string = "require_once(ABSPATH . 'wp-settings.php');"
#         self.terminating_string = terminating_string
#     def execute(self, worker, parameters):
#         session_id = parameters.get('_session_id', '1')
#         worker_client = worker.client()
#         output = worker_client.sessions.session(session_id).run_with_output(
#             self.command,
#             self.terminating_string,
#             timeout=30,
#             timeout_exception=True
#         )
#         print(output)

# class DumpWordpressConfigTechnique(ExecuteSessionCommandTechnique, CredentialAccessTactic):
#     """Dumps wp-config.php"""
#     def __init__(self, config_file_path):
#         command = f'cat {config_file_path}'
#         terminating_string = "require_once(ABSPATH . 'wp-settings.php');"
#         super().__init__(command, terminating_string)
#     def describe_flag(self):
#         return {
#             'kind': 'loot',
#             'type': 'linux.enum.conf',
#             'name': 'wp-config.php',
#         }

# class EnumerateNetworkAction(Action):
#     """
#     """
#     def __init__(self, target_cidr):
#         raise NotImplementedError('This is not yet implemented')
#         super().__init__(kind='msfrpc')
#         self.target_address = target_cidr.split('/')[0]
#         self.target_prefix = target_cidr.split('/')[-1] if '/' in target_cidr else '32'
#         self.commands = [
#             f'db_nmap {self.target_address}/{self.target_prefix}'
#         ]

#     def execute(self, worker_client):
#         pass
