# -*- coding: utf-8 -*-
"""
Workers module
"""

import shortuuid
import time
import logging
import json

from pymetasploit3.msfrpc import MsfRpcClient
from pymetasploit3.msfconsole import MsfRpcConsole

from .errors import ActionExecutionError
from .errors import ActionTimeoutError


logging.getLogger("urllib3").setLevel(logging.WARNING)


class Worker:
    """A worker
    """
    def __init__(self, appconfig, **kwargs):
        self.uid = f'w-{shortuuid.uuid()[:4]}'
        self.appconfig = appconfig

    def client(self, refresh=False):
        pass


class MsfRpcWorker(Worker):
    """A Metasploit worker via RPC api
    """
    def __init__(self, host, port, username, password, ssl, appconfig):
        super().__init__(appconfig)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self._client = None
        self._console = None
        self.console_positive_out = list()
        self.console_busy = False
        self.action_timeout = appconfig.action_timeout
        self.action_poll_timeout = appconfig.action_poll_timeout
        self.verbose = True

    def _read_console(self, console_data):
        self.console_busy = console_data['busy']
        if '[+]' in console_data['data']:
            sigdata = console_data['data'].rstrip().split('\n')
            for line in sigdata:
                if '[+]' in line:
                    self.console_positive_out.append(line)
        if self.verbose:
            print(f'\nOutput received (busy = {console_data["busy"]}) prompt={console_data["prompt"]}')
            print(f'{console_data["data"]}-EOF\n')

    def client(self, refresh=False):
        """Returns a client object for the worker
        """
        if not self._client or refresh:
            self._client = MsfRpcClient(
                self.password,
                username=self.username,
                server=self.host,
                port=self.port,
                ssl=self.ssl
            )
        return self._client

    def console(self):
        """Returns a console object for the worker
        """
        if not self._console:
            self._console = MsfRpcConsole(self.client(), cb=self._read_console)
        return self._console

    def execute(self, cmd, wait=True, timeout=None):
        """Runs commands, optionally waiting for output
        """
        if self.verbose:
            logging.debug(f'Executing: {cmd} (timeout={timeout})')
        self.console_busy = True
        self.console().execute(cmd)
        if wait:
            self.wait_console(timeout)

    def wait_console(self, timeout):
        """Waits until console command has finished
        """
        if not timeout:
            timeout = self.action_timeout
        timeout_stamp = time.time() + timeout
        while time.time() < timeout_stamp:
            if self.console_busy:
                # print('.', end='', flush=True)
                time.sleep(self.action_poll_timeout)
            else:
                return True
        logging.warning(
            'Timeout waiting for console output after %ss, aborting' % timeout)
        raise ActionTimeoutError

    def verify_goals(self, goals, target):
        """Goals is a list of dicts
        Any achieved item from the list causes achievement of overall Goals.
        All assert_* keys in a given dict must be achieved to achieve that goal.
        """
        for goal in goals['goals']:
            if self._verify_goal(goal, target):
                return True
        return False

    def _verify_goal(self, goal, target):
        interpolations = {
            '@TARGET@': target
        }
        print(f'Goal={goal}')
        for goal_key, goal_spec in goal.items():
            if goal_key.startswith('assert_'):
                kind = goal_key.split('assert_')[-1]
                try:
                    func_name = getattr(self, f'_find_{kind}s')
                    if not func_name(goal_spec, interpolations):
                        return False
                except AttributeError:
                    raise ValueError(f'Unknown kind "assert_{kind}" in Goal')
        return True

    def _find_services(self, properties, interpolations):
        """Find services with all the given properties"""
        services = self.client().call('db.services', opts=[{}])
        matching_services = []
        for service in services['services']:
            match = True
            for prop, value in properties.items():
                if value in interpolations:
                    value = interpolations[value]
                    value = service.get(prop)
                if not service.get(prop) or (service.get(prop) != value and value != '@NOTNULL@'):
                    match = False
                    break
            if match:
                matching_services.append(service)
        return matching_services

    def _find_hosts(self, properties, interpolations):
        """Find hosts with all the given properties"""
        hosts = self.client().call('db.hosts', opts=[{}])
        # print(f'All hosts={hosts}')
        matching_hosts = []
        for host in hosts['hosts']:
            match = True
            for prop, value in properties.items():
                if value in interpolations:
                    value = interpolations[value]
                    value = host.get(prop)
                if not host.get(prop) or (host.get(prop) != value and value != '@NOTNULL@'):
                    match = False
                    break
            if match:
                matching_hosts.append(host)
        return matching_hosts

    def _find_loots(self, properties, interpolations):
        """Find credentials with all the given properties"""
        loots = self.client().call('db.loots', opts=[{}])
        matching_loots = []
        for loot in loots['loots']:
            match = True
            for prop, value in properties.items():
                if value in interpolations:
                    value = interpolations[value]
                if not loot.get(prop) or loot.get(prop) != value:
                    match = False
                    break
            if match:
                matching_loots.append(loot)
        return matching_loots

    def _find_sessions(self, properties, interpolations):
        """Find a session with all the given properties"""
        # XXX filter sessions
        if self.client().sessions.list:
            # print(self.client().sessions.list)
            return next(iter(self.client().sessions.list.values()))
        return None
