#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
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

from enum import Enum
from wishbone.protocol.decode.dummy import Dummy as DummyDecoder
from wishbone.protocol.encode.dummy import Dummy as DummyEncoder


class ModuleType(Enum):
    INPUT = 1
    OUTPUT = 2
    FLOW = 3
    PROCESS = 4


class InputModule(object):
    MODULE_TYPE = ModuleType.INPUT
    decode = DummyDecoder().decode


class OutputModule(object):
    MODULE_TYPE = ModuleType.OUTPUT
    encode = DummyEncoder().encode


class FlowModule(object):
    MODULE_TYPE = ModuleType.FLOW


class ProcessModule(object):
    MODULE_TYPE = ModuleType.PROCESS
