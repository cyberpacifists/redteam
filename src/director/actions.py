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


from .errors import ActionExecutionError

class Action():
    def __init__(self, kind):
        self.kind = kind
    def execute(self, worker_client):
        pass


class ExecuteExploitAction(Action):
    """Executes an arbitrary exploit
    """
    def __init__(self, exploit_name, payload_name, options):
        super().__init__(kind='msfrpc')
        self.exploit_name = exploit_name
        self.payload_name = payload_name
        self.options = options

    def execute(self, worker_client):
        exploit = worker_client.modules.use('exploit', self.exploit_name)
        for key,value in self.options.items():
            exploit[key] = value
        # print(f'\noptions {exploit.options}')
        print(f'\nrequired options {exploit.required}')
        for option in exploit.required:
            print(f'    {option}: {exploit[option]}')
        # print(f'\npayloads {exploit.payloads}')
        job = exploit.execute(payload=self.payload_name)
        if job.get('job_id'):
            print(f'Exploit suceeded, job={job}')
            print("Sessions available: ")
            for s in worker_client.sessions.list.keys():
                print(s)
        else:
            raise ActionExecutionError('Failed to execute {} exploit (payload={}, options={}'.format(
                self.exploit_name, self.payload_name, self.options))
            print(f'Exploit failed, job={job}')
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

    def execute(self, client):
        pass


