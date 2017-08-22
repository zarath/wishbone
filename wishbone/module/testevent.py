#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  testevent.py
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

from wishbone.module import InputModule
from wishbone.protocol.decode.dummy import Dummy
from gevent import sleep
from wishbone.event import Event


class TestEvent(InputModule):

    '''**Generates a test event at the chosen interval.**

    The data field of the test event contains the string "test".


    Parameters:

        - interval(float)(1)
           |  The interval in seconds between each generated event.
           |  A value of 0 means as fast as possible.

        - payload(str/dict/int/float)("test")
           |  The content of the test message.

        - destination(str)("data")
           |  The location write the payload to

    Queues:

        - outbox
           |  Contains the generated events.
    '''

    def __init__(self, actor_config, interval=1, payload="test", destination="data"):
        InputModule.__init__(self, actor_config)
        self.pool.createQueue("outbox")
        self.decode = Dummy().handler

    def preHook(self):

        self.sendToBackground(self.produce)

    def produce(self):

        while self.loop():
            self.renderKwargs()
            for payload in self.decode(self.kwargs.payload):
                event = Event()
                event.set(payload, self.kwargs.destination)
                self.submit(event, "outbox")
                sleep(self.kwargs.interval)
        self.logging.info("Stopped producing events.")
