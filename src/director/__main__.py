# -*- coding: utf-8 -*-
"""
Director module entrypoint
"""

import os
from .main import main
from .config import Config

# @mention Dani, is this used in any way?
# import sys
# print(f'__main__.py Python path = {sys.path}')

appconfig = Config.from_environment(os.environ)
msfrpc_hosts = os.environ.get('MSFRPC_HOSTS').split(',')

main(appconfig, msfrpc_hosts)
