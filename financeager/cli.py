# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import subprocess
import Pyro4
import os
import sys
import time
from financeager.period import prettify
from financeager.server import TinyDbServer, CONFIG_DIR

Pyro4.config.COMMTIMEOUT = 1.0

class Cli(object):

    def __init__(self, cl_kwargs, server_cls=TinyDbServer):
        self._cl_kwargs = cl_kwargs
        self._server_cls = server_cls

        # launch nameserver. Silence errors if already running
        with open(os.devnull, 'w') as DEVNULL:
            subprocess.Popen("{} -m Pyro4.naming".format(sys.executable).split(),
                    stdout=DEVNULL, stderr=subprocess.STDOUT, close_fds=True)

        self._stacked_layout = self._cl_kwargs.pop("stacked_layout", False)

    def __call__(self):
        command = self._cl_kwargs.pop("command")

        if command == "list":
            self._print_list()
            return

        if command != "stop":
            self._start_period_server()

        server = Pyro4.Proxy("PYRONAME:{}".format(TinyDbServer.NAME))
        try:
            # server should be stateless and not storing response!
            server.run(command, **self._cl_kwargs)
            response = server.response
            if response is not None:
                error = response.get("error")
                if error is not None:
                    print(error)

                elements = response.get("elements")
                if elements is not None:
                    print(prettify(elements, self._stacked_layout))
        except (Pyro4.naming.NamingError) as e:
            # 'stop' requested but period server not launched
            pass

    def _start_period_server(self):
        name_server = Pyro4.locateNS()
        # launch starting script if period server is not registered yet
        try:
            name_server.lookup(TinyDbServer.NAME)
        except (Pyro4.naming.NamingError) as e:
            server_script_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "start_server.py")
            subprocess.Popen([sys.executable, server_script_path])
            # wait for launch to avoid failure when creating Proxy
            time.sleep(1.1*Pyro4.config.COMMTIMEOUT)

    def _print_list(self):
        running = self._cl_kwargs.pop("running", False)
        if running:
            name_server = Pyro4.locateNS()
            registered_servers = name_server.list()
            registered_servers.pop("Pyro.NameServer")
            for server in registered_servers:
                print(server)
                print()
        else:
            for file in os.listdir(CONFIG_DIR):
                filename, extension = os.path.splitext(file)
                if extension in [".xml", ".json"]:
                    print(filename)
                    print()
