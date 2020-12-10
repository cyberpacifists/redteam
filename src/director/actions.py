# -*- coding: utf-8 -*-
"""
Actions module.

Actions are each one of the steps that form a "Campaign".
Actions glue together a Technique, a Worker and a Target.
"""

import random
import socket
import logging
import time
import uuid

from .errors import ActionExecutionError


class Action():
    def __init__(
        self,
        phase,
        name,
        technique,
        goals,
        targets=None,
        targets_query=None,
        max_targets=10,
        wait=True,
        timeout=None
    ):
        self.uid = f'a-{str(uuid.uuid4())[-4:]}'
        self.phase = phase
        self.name = name
        self.technique = technique
        self.goals = goals
        self.targets = set(targets) if targets else set()
        self.targets_query = targets_query
        self.max_targets = max_targets
        self.wait = wait
        self.timeout = timeout
        self.attempts = 0
        self.succeeded = False
        self._session_id = None # XXX remove
        if not targets and not targets_query:
            raise ValueError(
                'An Action requires either a list of targets or a target query expression'
            )

    def find_targets(self, worker):
        # XXX implement in workers
        # either use resource files (rc/ruby/python)
        # or use simple commands like vulns, then parse in this python
        if 'session' in self.targets_query:
            self.targets.add('172.19.0.7')
            session_id = list(worker.client().sessions.list.keys())[-1]
            print(f'Found session={session_id}')
            self._session_id = session_id
            return session_id
        if not self.targets:
            self.targets = set([
                '172.19.0.3',
                '172.19.0.4',
                '172.19.0.5',
                '172.19.0.6',
                '172.19.0.7',
                '172.19.0.8',
            ])
        return self.targets

    def execute(self, worker):
        if not self.targets:
            self.find_targets(worker)
        execution_targets = random.sample(
            self.targets,
            min(len(self.targets), self.max_targets)
        )
        parameters = {
            'RHOSTS': ','.join(execution_targets),
        }
        if self._session_id:
            parameters['SESSION'] = self._session_id
        kwargs = {}
        if self.wait:
            kwargs['wait'] = self.wait
        if self.timeout:
            kwargs['timeout'] = self.timeout
        self.technique.execute(worker, parameters, **kwargs)

    def verify_goals(self, worker, refresh=False):
        if self.succeeded and not refresh:
            return True
        for target in self.targets:
            if worker.verify_goals(self.goals, target):
                logging.info(f'Goal achieved for target {target}')
                self.succeeded = True
                return True
        self.succeeded = False
        return False

    def __str__(self):
        return f'{self.uid} ({self.phase}/{self.name})'
