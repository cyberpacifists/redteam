# -*- coding: utf-8 -*-
"""
Director module entrypoint
"""

import os
import sys

from .main import main
from .config import Config

print(f'__main__.py Python path = {sys.path}')

appconfig = Config.from_environment(os.environ)
msfrpc_hosts = os.environ['MSFRPC_HOSTS'].split(',')

main(appconfig, msfrpc_hosts)
