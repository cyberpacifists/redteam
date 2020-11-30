# -*- coding: utf-8 -*-
"""
Actions module

to-do: Consider stealth level of actions / implement those at campaign level

to-do: more actions like below

# print(client.call('db.hosts'))
    # print(client.sessions.list)
    # print(result)
    # shell = client.sessions.session('1')
    # shell.write('whoami')
    # print(shell.read())
"""

import logging
import time

from .errors import ActionExecutionError

class Action():
    def __init__(self, kind):
        self.kind = kind
    def execute(self, worker):
        pass
    def execute_rpc(self, worker_client):
        pass


class ExecuteExploitAction(Action):
    """Executes an arbitrary exploit
    """
    def __init__(self, exploit_name, payload_name, options):
        super().__init__(kind='msfrpc')
        self.exploit_name = exploit_name
        self.payload_name = payload_name
        self.options = options

    def execute(self, worker):
        worker_client = worker.client()
        worker.execute('sessions\n', wait=True)
        commands = [
            f'use exploits/{self.exploit_name}'
        ]
        for key,value in self.options.items():
            commands.append(f'set {key} {value}')
        commands.append('options')
        # commands.append('show payloads')
        if self.payload_name:
            commands.append(f'set payload {self.payload_name}')
        worker.verbose = True
        commands.append('run -z')
        worker.execute('\n'.join(commands), wait=True)
        print("Sessions available: ")
        for s in worker_client.sessions.list.keys():
            print(s)
        worker.execute('sessions\n', wait=True)
        # else:
        #     raise ActionExecutionError('Failed to execute {} exploit (payload={}, options={}'.format(
        #         self.exploit_name, self.payload_name, self.options))
        #     # print(f'Exploit failed, job={job}')
        # return job

    def execute_rpc(self, worker_client):
        exploit = worker_client.modules.use('exploit', self.exploit_name)
        for key,value in self.options.items():
            exploit[key] = value
        # print(f'\noptions {exploit.options}')
        print(f'\nrequired options {exploit.required}')
        for option in exploit.required:
            print(f'    {option}: {exploit[option]}')
        # print(f'\npayloads {exploit.payloads}')
        if self.payload_name:
            job = exploit.execute(payload=self.payload_name)
            # # import pdb; pdb.set_trace()
            # stdout = worker_client.consoles.console().run_module_with_output(exploit, payload=self.payload_name)
            # print(stdout)
        else:
            job = exploit.execute()
        if job.get('job_id'):
            print(f'Exploit suceeded, job={job}')
            print("Sessions available: ")
            for s in worker_client.sessions.list.keys():
                print(s)
        else:
            raise ActionExecutionError('Failed to execute {} exploit (payload={}, options={}'.format(
                self.exploit_name, self.payload_name, self.options))
            # print(f'Exploit failed, job={job}')
        return job


class EnumerateNetworkAction(Action):
    """
    """
    def __init__(self, target_cidr):
        raise NotImplementedError('This is not yet implemented')
        super().__init__(kind='msfrpc')
        self.target_address = target_cidr.split('/')[0]
        self.target_prefix = target_cidr.split('/')[-1] if '/' in target_cidr else '32'
        self.commands = [
            f'db_nmap {self.target_address}/{self.target_prefix}'
        ]

    def execute(self, worker_client):
        pass


class ExecuteSessionCommandAction(Action):
    """Executes an arbitrary command in a session
    """
    def __init__(self, cmd):
        super().__init__(kind='msfrpc')
        self.cmd = cmd
        self.terminating_string = "require_once(ABSPATH . 'wp-settings.php');"

    def execute(self, worker):
        session_id = '1'
        worker_client = worker.client()
        output = worker_client.sessions.session(session_id).run_with_output(
            self.cmd,
            self.terminating_string,
            timeout=30,
            timeout_exception=True
        )
        print(output)