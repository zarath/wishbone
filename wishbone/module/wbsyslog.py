#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  wbsyslog.py
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

from wishbone.actor import Actor
from wishbone.module import OutputModule
from wishbone.event import Bulk
import syslog
import sys
import os


class Syslog(OutputModule):

    '''**Writes log events to syslog.**

    Logevents have following format:

    (6, 1367682301.430527, 'Router', 'Received SIGINT. Shutting down.')

    The first value corresponds to the syslog severity level.

    Parameters:

        - level(int)(5)*
           |  The loglevel.
           |  (Can be a dynamic value)

        - ident(str)(<script_name>)*
           |  The syslog id string.
           |  If not provided the script name is used.
           |  (Can be a dynamic value)

        - message(str)("{@data[message]}")*
           |  The syslog id string.
           |  If not provided the script name is used.
           |  (Can be a dynamic value)

    Queues:

        - inbox
           |  incoming events
    '''

    def __init__(self, actor_config, level=5, ident=os.path.basename(sys.argv[0]), message="{@data[message]}"):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.registerConsumer(self.consume, "inbox")

    def preHook(self):

        syslog.openlog("%s[%s]" % (self.kwargs.ident, os.getpid()))

    def consume(self, event):

        if isinstance(event, Bulk):
            for e in event.dump():
                message = e.format(self.kwargs.message, '.')
                level = e.format(self.kwargs.level, '.')
                syslog.syslog(level, message)
        else:
            message = event.format(self.kwargs.message, '.')
            level = event.format(self.kwargs.level, '.')
            syslog.syslog(level, message)

    def postHook(self):
        syslog.closelog()
