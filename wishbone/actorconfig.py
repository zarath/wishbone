#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  actorconfig.py
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


class ActorConfig(object):

    '''
    A configuration object pass to a Wishbone actor.

    This is a simple object which holds a set of attributes (with some sane
    defaults) a Wishbone Actor expects.

    Attributes:
        name (str): The name identifying the actor instance.
        size (int): The size of the Actor instance's queues.
        frequency (int): The time in seconds to generate metrics.
        lookups (dict): A dictionary of lookup methods.
        description (str): A short free form discription of the actor instance.
        functions (dict): A dict of queue names containing an array of functions
        protocol_name (str): A protocol decode or encode component name.
        protocol_function (func): The protocol function to apply
        protocol_event (bool): If true the incoming data is expected to be a Wishbone event.
        disable_exception_handling (bool): If True, exception handling is disabled. Usefull for testing
    '''

    def __init__(self, name, size=100, frequency=1, lookups={}, description="A Wishbone actor.", functions={},
                 protocol_name=None, protocol_function=None, protocol_event=False,
                 disable_exception_handling=False):

        '''
        Args:
            name (str): The name identifying the actor instance.
            size (int): The size of the Actor instance's queues.
            frequency (int): The time in seconds to generate metrics.
            lookups (dict): A dictionary of lookup methods.
            description (str): A short free form discription of the actor instance.
            functions (dict): A dict of queue names containing an array of functions.
            protocol_name (str): A protocol decode or encode component name.
            protocol_function (func): The protocol function to apply
            protocol_event (bool): If true the incoming data is expected to be a Wishbone event.
            disable_exception_handling (bool): If True, exception handling is disabled. Usefull for testing
        '''
        self.name = name
        self.size = size
        self.frequency = frequency
        self.lookups = lookups
        self.description = description
        self.functions = functions
        self.protocol_name = protocol_name
        self.protocol_function = protocol_function
        self.protocol_event = protocol_event
        self.disable_exception_handling = disable_exception_handling
