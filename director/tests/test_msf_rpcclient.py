# -*- coding: utf-8 -*-

import pytest

from director.config import Config
from director.workers import MsfRpcWorker


def test_fib():
    appconfig = Config.from_environment({})
    host = 'localhost:55553'
    worker = MsfRpcWorker(
        host=host.split(':')[0],
        port=int(host.split(':')[-1]) if ':' in host else 55553,
        username='auser',
        password='somepassword',
        ssl=False,
        appconfig=appconfig
    )
    # with pytest.raises(AssertionError):
    #     worker.client()
