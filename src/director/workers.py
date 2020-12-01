# -*- coding: utf-8 -*-
"""
Workers module
"""

import uuid
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
        self.id = uuid.uuid4()  # pylint: disable=invalid-name
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
        print(f'\nOutput received\nbusy = {console_data["busy"]}')
        print(f'{console_data["prompt"]}')
        self.console_busy = console_data['busy']
        if '[+]' in console_data['data']:
            sigdata = console_data['data'].rstrip().split('\n')
            for line in sigdata:
                if '[+]' in line:
                    self.console_positive_out.append(line)
        if self.verbose:
            print(console_data['data'])

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

    def execute(self, cmd, wait=True):
        """Runs commands, optionally waiting for output
        """
        if self.verbose:
            logging.debug(f'Executing: {cmd}')
        self.console_busy = True
        self.console().execute(cmd)
        if wait:
            self.wait_console()

    def wait_console(self):
        """Waits until console command has finished
        """
        timeout_stamp = time.time() + self.action_timeout
        while time.time() < timeout_stamp:
            if self.console_busy:
                print('.', end='')
                time.sleep(self.action_poll_timeout)
            else:
                print('-CommandCompleted')
                return True
        logging.warning(
            'Timeout waiting for console output after %ss, aborting' % self.action_timeout)
        raise ActionTimeoutError


# def wait_tcp_port(host, port, timeout, connect_timeout=5, retry_interval=5, logger=None):
#     """
#     """
#     if not logger:
#         logger = logging.getLogger(__name__)
#         logger.setLevel(LOGLEVEL_DEFAULT)
#     logger.info('Waiting for TCP port to be available ({}:{}) (max wait {}s, interval {}s)'.format(host, port, timeout, retry_interval))
#     timeout_stamp = time.time() + timeout
#     attempts = 0
#     while time.time() < timeout_stamp:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#             sock.settimeout(  int(connect_timeout)  )
#             try:
#                 attempts += 1
#                 logger.debug('Trying connection to {}:{} (attempt {})'.format(host, port, attempts))
#                 sock.connect((host, port))
#                 logger.info('TCP port {}:{} available after {} attempts'.format(host, port, attempts))
#                 return True
#             except Exception as e1:
#                 logger.debug('Could not connect to {}:{} {}'.format(host, port, e1))
#                 time.sleep(  int(retry_interval)  )
#     logger.warning('Failed to reach TCP port {}:{} after {} attempts in {} seconds'.format(host, port, attempts, timeout))
#     return False

# if not wait_tcp_port(worker['host'], worker['port'], 5):
#     print('TCP service is not available')
#     logging.critical('TCP service is not available')
#     raise RuntimeError()
# logging.info('Port is reachable')
# print('RPC Port is reachable')