#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  actor.py
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

from wishbone.queue import QueuePool
from wishbone.logging import Logging
from wishbone.event import Event as Wishbone_Event
from wishbone.event import Metric
from wishbone.event import Bulk
from wishbone.error import QueueConnected, ModuleInitFailure, InvalidModule, TTLExpired
from wishbone.moduletype import ModuleType
from wishbone.actorconfig import ActorConfig

from collections import namedtuple
from gevent import spawn, kill
from gevent import sleep, socket
from gevent.event import Event
from wishbone.error import QueueFull
from time import time
from sys import exc_info
import traceback
import inspect
from easydict import EasyDict
import jinja2

Greenlets = namedtuple('Greenlets', "consumer generic log metric")


class Actor(object):

    def __init__(self, config):

        self.config = config
        self.name = config.name
        self.size = config.size
        self.frequency = config.frequency
        self.description = config.description

        self.pool = QueuePool(config.size)

        self.logging = Logging(config.name, self.pool.queue.logs)

        self.__loop = True
        self.greenlets = Greenlets([], [], [], [])
        self.greenlets.metric.append(spawn(self.metricProducer))

        self.__run = Event()
        self.__run.clear()

        self.__connections = {}

        self.__children = {}
        self.__parents = {}

        self.__lookups = {}

        self.stopped = True

        self.__current_event = {}
        self.raw_kwargs = {}
        self.kwargs = EasyDict({})

        self.__setupKwargs()

    def connect(self, source, destination_module, destination_queue):
        '''Connects the <source> queue to the <destination> queue.
        In fact, the source queue overwrites the destination queue.'''

        if source in self.__children:
            raise QueueConnected("Queue %s.%s is already connected to %s." % (self.name, source, self.__children[source]))
        else:
            self.__children[source] = "%s.%s" % (destination_module.name, destination_queue)

        if destination_queue in destination_module.__parents:
            raise QueueConnected("Queue %s.%s is already connected to %s" % (destination_module.name, destination_queue, destination_module.__parents[destination_queue]))
        else:
            destination_module.__parents[destination_queue] = "%s.%s" % (self.name, source)

        if not self.pool.hasQueue(source):
            self.logging.debug("Module instance '%s' has no queue '%s' so auto created." % (self.name, source))
            self.pool.createQueue(source)

        if not destination_module.pool.hasQueue(destination_queue):
            self.logging.debug("Module instance '%s' has no queue '%s' so auto created." % (destination_module.name, destination_queue))

        setattr(destination_module.pool.queue, destination_queue, self.pool.getQueue(source))
        self.pool.getQueue(source).disableFallThrough()
        self.logging.debug("Connected queue %s.%s to %s.%s" % (self.name, source, destination_module.name, destination_queue))

    def getChildren(self, queue=None):
        '''Returns the queue name <queue> is connected to.'''

        if queue is None:
            return [self.__children[q] for q in list(self.__children.keys())]
        else:
            return self.__children[queue]

    def loop(self):
        '''The global lock for this module'''

        return self.__loop

    def metricProducer(self):
        '''A greenthread which collects the queue metrics at the defined interval.'''

        self.__run.wait()
        hostname = socket.gethostname()
        while self.loop():
            for queue in self.pool.listQueues(names=True):
                for metric, value in list(self.pool.getQueue(queue).stats().items()):
                    metric = Metric(time=time(),
                                    type="wishbone",
                                    source=hostname,
                                    name="module.%s.queue.%s.%s" % (self.name, queue, metric),
                                    value=value,
                                    unit="",
                                    tags=())
                    event = Wishbone_Event(metric)
                    self.submit(event, self.pool.queue.metrics)
            sleep(self.frequency)

    def postHook(self):

        pass

    def preHook(self):

        self.logging.debug("Initialized.")

    def renderKwargs(self, event=None):

        if event is None:
            for name, template in self.raw_kwargs.items():
                self.kwargs[name] = template.render(self.__current_event)
        else:
            for name, template in self.raw_kwargs.items():
                self.kwargs[name] = template.render(event.dump(complete=True))

    def registerConsumer(self, function, queue):
        '''Registers <function> to process all events in <queue>

        Do not trap errors.  When <function> fails then the event will be
        submitted to the "failed" queue,  If <function> succeeds to the
        success queue.'''

        self.greenlets.consumer.append(spawn(self.__consumer, function, queue))

    def start(self):
        '''Starts the module.'''

        self.__setProtocolMethod()

        if hasattr(self, "preHook"):
            self.logging.debug("preHook() found, executing")
            self.preHook()
        self.__validateAppliedFunctions()
        self.__run.set()
        self.logging.debug("Started with max queue size of %s events and metrics interval of %s seconds." % (self.size, self.frequency))
        self.stopped = False

    def sendToBackground(self, function, *args, **kwargs):
        '''Executes a function and sends it to the background.

        Background tasks are usually running indefinately. When such a
        background task generates an error, it is automatically restarted and
        an error is logged.
        '''

        def wrapIntoLoop():
            while self.loop():
                try:
                    function(*args, **kwargs)
                    # We want to break out of the loop if we get here because
                    # it's the intention of function() to exit without errors.
                    # Normally, background tasks run indefinately but in this
                    # case the user opted not to for some reason so we should
                    # obey that.
                    break
                except Exception as err:
                    if self.config.disable_exception_handling:
                        raise
                    self.logging.error("Backgrounded function '%s' of module instance '%s' caused an error. This needs attention. Restarting it in 2 seconds. Reason: %s" % (
                        function.__name__,
                        self.name,
                        err)
                    )
                    sleep(2)

        self.greenlets.generic.append(spawn(wrapIntoLoop))

    def stop(self):
        '''Stops the loop lock and waits until all registered consumers have exit otherwise kills them.'''

        self.logging.info("Received stop. Initiating shutdown.")

        self.__loop = False

        for background_job in self.greenlets.metric:
            kill(background_job)

        for background_job in self.greenlets.generic:
            kill(background_job)

        for background_job in self.greenlets.consumer:
            kill(background_job)

        if hasattr(self, "postHook"):
            self.logging.debug("postHook() found, executing")
            self.postHook()

        self.logging.debug("Exit.")

        self.stopped = True

    def submit(self, event, queue):
        '''A convenience function which submits <event> to <queue>.'''

        while self.loop():
            try:
                queue.put(event)
                break
            except QueueFull:
                sleep(0.1)

    def __applyFunctions(self, queue, event):

        if queue in self.config.functions:
            for f in self.config.functions[queue]:
                try:
                    event = f(event)
                except Exception as err:
                    if self.config.disable_exception_handling:
                        raise
                    self.logging.error("Function '%s' is skipped as it is causing an error. Reason: '%s'" % (f.__name__, err))
        return event

    def __consumer(self, function, queue):
        '''Greenthread which applies <function> to each element from <queue>
        '''

        self.__run.wait()
        self.logging.debug("Function '%s' has been registered to consume queue '%s'" % (function.__name__, queue))

        while self.loop():
            event = self.pool.queue.__dict__[queue].get()
            self.__current_event = event.dump(complete=True)
            self.renderKwargs()
            try:
                event.decrementTTL()
            except TTLExpired as err:
                self.logging.warning("Event with UUID %s dropped. Reason: %s" % (event.get("uuid"), err))
                continue

            event = self.__applyFunctions(queue, event)
            self.current_event = event

            try:
                function(event)
            except Exception as err:
                if self.config.disable_exception_handling:
                    raise
                exc_type, exc_value, exc_traceback = exc_info()
                info = (traceback.extract_tb(exc_traceback)[-1][1], str(exc_type), str(exc_value))

                if isinstance(event, Wishbone_Event):
                    event.set(info, "errors.%s" % (self.name))
                elif(event, Bulk):
                    event.error = info

                self.logging.error("%s" % (err))
                self.submit(event, self.pool.queue.failed)
            else:
                self.submit(event, self.pool.queue.success)

            if isinstance(event, Bulk):
                for e in event.dump():
                    if self.name in e.confirmation_modules:
                        e.confirm()
            else:
                if self.name in event.confirmation_modules:
                    event.confirm()

    def __generateEventWithPayload(self, data={}):

        '''
        Generates a new event with payload <data>.
        '''

        return Wishbone_Event(data, confirmation_modules=self.config.confirmation_modules)

    def __generateEvent(self, data={}):

        '''
        Generates a new event from <data>. <data> is supposed to contain the
        metadata fields too.
        '''

        e = Wishbone_Event(confirmation_modules=self.config.confirmation_modules)
        e.slurp(data)
        return e

    def __validateAppliedFunctions(self):

        '''
        A validation routine which checks whether functions have been applied
        to queues without a registered consumer.  The effect of that would be
        that the functions are never applied which is not what the user
        wanted.
        '''

        queues_w_registered_consumers = [t.args[1] for t in self.greenlets.consumer]

        for queue in self.config.functions.keys():
            if queue not in queues_w_registered_consumers:
                raise ModuleInitFailure("Failed to initialize module '%s'. You have functions defined on queue '%s' which doesn't have a registered consumer." % (self.name, queue))

    def __setProtocolMethod(self):

        '''Checks whether the module is of type input or output and whether it
        has a protocol encoder/decoder set.'''

        if not hasattr(self, "MODULE_TYPE"):
            raise InvalidModule("Module instance '%s' seems to be of an incompatible old type." % (self.name))

        if self.MODULE_TYPE == ModuleType.INPUT:
            if not hasattr(self, "decode") and self.config.protocol_name is None:
                self.logging.debug("This 'Input' type module has no decoder method set. Setting dummy decoder.")
                self.setDecoder("wishbone.protocol.decode.dummy")
            if self.config.protocol_name is not None:
                self.logging.debug("This 'Input' type module has no decoder method set. Setting the configured one.")
                self.decode = self.config.protocol_function

            if self.config.protocol_event is True:
                self.generateEvent = self.__generateEvent
            else:
                self.generateEvent = self.__generateEventWithPayload

        if self.MODULE_TYPE == ModuleType.OUTPUT:
            if not hasattr(self, "encode") and self.config.protocol_name is None:
                self.logging.debug("This 'Output' type module has no encoder method set. Setting dummy encoder.")
                self.setEncoder("wishbone.protocol.encode.dummy")
            if self.config.protocol_name is not None:
                self.logging.debug("This 'Output' type module has no encoder method set. Setting the configured one.")
                self.encode = self.config.protocol_function

    def __setupKwargs(self):

        '''
        Initial rendering of all templates to self.kwargs
        '''

        for key, template in list(inspect.getouterframes(inspect.currentframe())[2][0].f_locals.items()):
            if key == "self" or isinstance(template, ActorConfig):
                next
            else:
                if isinstance(template, str):
                    self.raw_kwargs[key] = jinja2.Template(template)
                    for name, function in self.config.lookup.items():
                        self.raw_kwargs[key].globals[name] = function
                    try:
                        self.kwargs[key] = self.raw_kwargs[key].render(data={})
                    except Exception:
                        self.kwargs[key] = self.raw_kwargs[key]
                else:
                    self.kwargs[key] = template
