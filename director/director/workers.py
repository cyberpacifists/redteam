# -*- coding: utf-8 -*-
"""
Workers module
"""

import uuid

from pymetasploit3.msfrpc import MsfRpcClient


class Worker():
    """A worker
    """
    def __init__(self, appconfig, **kwargs):
        self.id = uuid.uuid4()
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