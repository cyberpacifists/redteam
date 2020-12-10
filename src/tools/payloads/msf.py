#!/usr/bin/env python

import os
import sys
import time

from pymetasploit3.msfrpc import MsfRpcClient
from pymetasploit3.msfconsole import MsfRpcConsole


class MsfRpcWorker:
    """ Metasploit worker """

    _host = os.environ.get("MSF_HOST", "msf")
    _username = os.environ.get("MSF_USER", "username")
    _password = os.environ.get("MSF_PSW", "password")
    _port = os.environ.get("MSF_PORT", 55553)
    _ssl: bool = True
    _busy: bool = True
    _welcome_message: bool = True

    def __init__(self):
        # establish teh connection with the host running metasploit
        self._client = MsfRpcClient(
            username=self._username,
            password=self._password,
            server=self._host,
            port=self._port,
            ssl=self._ssl,
        )

        # create a console in where we can execute commands
        self._console = MsfRpcConsole(
            rpc=self._client,
            cb=self.read,
        )

    def read(self, output):
        """ callback function which updates the state of the console and prints any data given to him """
        if self._welcome_message:
            # consume the welcome message, which puts the console to rest.
            self._welcome_message = False
            return

        self._busy = output["busy"]
        print(output["data"])

    def execute(self, cmd):
        self._console.execute(command=cmd,)

    def db_get(self, command, options=None):
        """ Print the loot generated within this session """
        q = self._client.call(f"db.{command}", opts=options if options else [{}])
        return q

    def timeout(self, seconds):
        """ Attempt to destroy the console connection and exit the program """
        while self._busy:
            time.sleep(seconds)

        try:
            # the program needs to be stopped somehow, this is a temporary fix which attempts to destroy the current
            # console and terminate the connection.
            # It throws an error!
            self._console.console.destroy()
        except Exception:
            sys.exit()


if __name__ == '__main__':
    # initiate the worker
    worker = MsfRpcWorker()

    # capture the arguments given with the payload
    commands = sys.argv[1:]

    for c in commands:
        worker.execute(cmd=c)

    # make the process to run until the console has finished, and destroy it
    worker.timeout(3)
