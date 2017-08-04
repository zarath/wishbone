#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_module_jsonencode.py
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

from wishbone.componentmanager import ComponentManager
from wishbone.event import Event

def test_wishbone_function_modify_uppercase():

    e = Event({"case": "upper"})
    f = ComponentManager().getComponentByName("wishbone.function.modify.uppercase")("data.case", "data.case")
    assert f(e).get() == {"case": "UPPER"}

def test_wishbone_function_modify_lowercase():

    e = Event({"case": "LOWER"})
    f = ComponentManager().getComponentByName("wishbone.function.modify.lowercase")("data.case", "data.case")
    assert f(e).get() == {"case": "lower"}

def test_wishbone_function_process_set():

    e = Event({"hey": "how"})
    f = ComponentManager().getComponentByName("wishbone.function.modify.set")({"greeting": "hello"}, "tmp.test")
    assert f(e).get("tmp.test") == {"greeting": "hello"}
