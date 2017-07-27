#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  default.py
#
#  Copyright 2017 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from wishbone.actorconfig import ActorConfig
from wishbone.error import ModuleInitFailure, NoSuchModule, ProtocolInitFailure
from wishbone.componentmanager import ComponentManager
from gevent import event, sleep, spawn
from gevent import pywsgi
import json
from .graphcontent import GRAPHCONTENT
from .graphcontent import VisJSData


class Container():
    pass


class ModulePool():

    def __init__(self):

        self.module = Container()

    def list(self):
        '''Returns a generator returning all module instances.'''

        for m in list(self.module.__dict__.keys()):
            yield self.module.__dict__[m]

    def getModule(self, name):
        '''Returns a module instance'''

        try:
            return getattr(self.module, name)
        except AttributeError:
            raise NoSuchModule("Could not find module %s" % name)


class Default(object):

    '''The default Wishbone router.

    A Wishbone router is responsible for shoveling the messages from one
    module to the other.

    Args:
        config (obj): The router setup configuration.
        size (int): The size of all queues.
        frequency (int)(1): The frequency at which metrics are produced.
        identification (wishbone): A string identifying this instance in logging.
    '''

    def __init__(self, config=None, size=100, frequency=1, identification="wishbone", graph=False, graph_include_sys=False):

        self.component_manager = ComponentManager()
        self.config = config
        self.size = size
        self.frequency = frequency
        self.identification = identification
        self.graph = graph
        self.graph_include_sys = graph_include_sys

        self.module_pool = ModulePool()
        self.__block = event.Event()
        self.__block.clear()

    def block(self):
        '''Blocks until stop() is called and the shutdown process ended.'''

        self.__block.wait()

    def connectQueue(self, source, destination):
        '''Connects one queue to the other.

        For convenience, the syntax of the queues is <modulename>.<queuename>
        For example:

            stdout.inbox

        Args:
            source (str): The source queue in <module.queue_name> syntax
            destination (str): The destination queue in <module.queue_name> syntax
        '''

        (source_module, source_queue) = source.split('.')
        (destination_module, destination_queue) = destination.split('.')

        source = self.module_pool.getModule(source_module)
        destination = self.module_pool.getModule(destination_module)

        source.connect(source_queue, destination, destination_queue)

    def getChildren(self, module):
        '''Returns all the connected child modules

        Args:
            module (str): The name of the module.

        Returns:
            list: A list of module names.
        '''
        children = []

        def lookupChildren(module, children):
            for module in self.module_pool.getModule(module).getChildren():
                name = module.split(".")[0]
                if name not in children:
                    children.append(name)
                    lookupChildren(name, children)

        try:
            lookupChildren(module, children)
        except NoSuchModule:
            return []
        else:
            return children

    def registerModule(self, module, actor_config, arguments={}):
        '''Initializes the wishbone module module.

        Args:
            module (Actor): A Wishbone module object (not initialized)
            actor_config (ActorConfig): The module's actor configuration
            arguments (dict): The parameters to initialize the module.
        '''

        try:
            setattr(self.module_pool.module, actor_config.name, module(actor_config, **arguments))
        except Exception as err:
            raise ModuleInitFailure("Problem loading module %s.  Reason: %s" % (actor_config.name, err))

    def stop(self):
        '''Stops all running modules.'''

        for module in self.module_pool.list():
            if module.name not in self.getChildren("_logs") + ["_logs"] and not module.stopped:
                module.stop()

        while not self.__logsEmpty():
            sleep(0.1)

        self.__running = False
        self.__block.set()

    def start(self):
        '''Starts all registered modules.'''

        if self.config is not None:
            self.__initConfig()

        if self.graph:
            self.graph = GraphWebserver(self.config, self.module_pool, self.__block, self.graph_include_sys)
            self.graph.start()

        for module in self.module_pool.list():
            module.start()

    def __initConfig(self):
        '''Setup all modules and routes.'''

        protocols = {}

        for name, instance in list(self.config.protocols.items()):
            try:
                protocols[name] = self.component_manager.getComponentByName(instance.protocol)(**instance.arguments).handler
            except Exception as err:
                raise ProtocolInitFailure("Could not initialize Protocol module '%s'. Reason: %s" % (name, err))

        lookups = {}
        for name, instance in list(self.config.lookups.items()):
            lookups[name] = self.component_manager.getComponentByName(instance.lookup)(**instance.arguments).lookup

        functions = {}
        for name, instance in list(self.config.functions.items()):
            self.component_manager.getComponentByName(instance.function)
            functions[name] = self.component_manager.getComponentByName(instance.function)(**instance.arguments)

        for name, instance in list(self.config.modules.items()):
            # Cherrypick the defined functions
            module_functions = {}
            for queue, queue_functions in list(instance.functions.items()):
                module_functions[queue] = []
                for queue_function in queue_functions:
                    if queue_function in functions:
                        module_functions[queue].append(functions[queue_function])

            pmodule = self.component_manager.getComponentByName(instance.module)

            if instance.description == "":
                instance.description = pmodule.__doc__.split("\n")[0].replace('*', '')

            protocol_name = instance.get("protocol", None)
            protocol_function = protocols.get(protocol_name, None)
            protocol_event = self.config.protocols.get(protocol_name, {}).get("event", False)

            actor_config = ActorConfig(
                name=name,
                size=self.size,
                frequency=self.frequency,
                lookups=lookups,
                description=instance.description,
                functions=module_functions,
                identification=self.identification,
                protocol_name=protocol_name,
                protocol_function=protocol_function,
                protocol_event=protocol_event
            )

            self.registerModule(pmodule, actor_config, instance.arguments)

        self.__setupConnections()

    def __logsEmpty(self):
        '''Checks each module whether any logs have stayed behind.'''

        for module in self.module_pool.list():
            if not module.pool.queue.logs.size() == 0:
                return False
        else:
            return True

    def __setupConnections(self):
        '''Setup all connections as defined by configuration_manager'''

        for route in self.config.routingtable:
            self.connectQueue("%s.%s" % (route.source_module, route.source_queue), "%s.%s" % (route.destination_module, route.destination_queue))


class GraphWebserver():

    def __init__(self, config, module_pool, block, include_sys):
        self.config = config
        self.module_pool = module_pool
        self.block = block
        self.js_data = VisJSData()

        for c in self.config["routingtable"]:
                self.js_data.addModule(instance_name=c.source_module,
                                       module_name=self.config["modules"][c.source_module]["module"],
                                       description=self.module_pool.getModule(c.source_module).description)

                self.js_data.addModule(instance_name=c.destination_module,
                                       module_name=self.config["modules"][c.destination_module]["module"],
                                       description=self.module_pool.getModule(c.destination_module).description)

                self.js_data.addQueue(c.source_module, c.source_queue)
                self.js_data.addQueue(c.destination_module, c.destination_queue)
                self.js_data.addEdge("%s.%s" % (c.source_module, c.source_queue), "%s.%s" % (c.destination_module, c.destination_queue))

    def start(self):

        print("#####################################################")
        print("#                                                   #")
        print("# Caution: Started webserver on port 8088           #")
        print("#                                                   #")
        print("#####################################################")
        spawn(self.setupWebserver)

    def stop(self):
        pass

    def loop(self):

        return self.__block

    def getMetrics(self):

        def getConnectedModuleQueue(m, q):
            for c in self.config["routingtable"]:
                if c.source_module == m and c.source_queue == q:
                    return (c.destination_module, c.destination_queue)
            return (None, None)

        d = {"module": {}}
        for module in self.module_pool.list():
            d["module"][module.name] = {}
            for queue in module.pool.listQueues(names=True):
                d["module"][module.name]["queue"] = {queue: {"metrics": module.pool.getQueue(queue).stats()}}
                (dest_mod, dest_q) = getConnectedModuleQueue(module.name, queue)
                if dest_mod is not None and dest_q is not None:
                    d["module"][module.name]["queue"] = {queue: {"connection": {"module": dest_mod, "queue": dest_q}}}
        return json.dumps(d)

    def application(self, env, start_response):
        if env['PATH_INFO'] == '/':
            start_response('200 OK', [('Content-Type', 'text/html')])
            return[GRAPHCONTENT % (self.js_data.dumpString()[0], self.js_data.dumpString()[1])]
        elif env['PATH_INFO'] == '/metrics':
            start_response('200 OK', [('Content-Type', 'text/html')])
            return[self.getMetrics()]
        else:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<h1>Not Found</h1>']

    def setupWebserver(self):

        pywsgi.WSGIServer(('', 8088), self.application, log=None, error_log=None).serve_forever()
