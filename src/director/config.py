# -*- coding: utf-8 -*-
"""
Configuration module
"""

import sys
import logging


class Config():

    @classmethod
    def from_environment(cls, env):
        """Creates config from an environment dictionary
        """
        cls.loglevel = env.get('LOGLEVEL', 'INFO')
        cls.speed = max(1, min(100, int(env.get('SPEED', '90'))))
        cls.turn_sleep = max(1, 100 - cls.speed)
        cls.setup_logging(cls.loglevel)
        cls.log_director = logging.getLogger('director')
        cls.log_decision = logging.getLogger('decision')
        # to-do: mock an event bus instead of a campaign log
        # cls.log_campaign = logging.getLogger('campaign')
        return cls

    @classmethod
    def setup_logging(cls, loglevel):
        """Setup basic logging
        """
        logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
        logging.basicConfig(level=loglevel, stream=sys.stdout,
                            format=logformat, datefmt="%Y-%m-%d %H:%M:%S")
