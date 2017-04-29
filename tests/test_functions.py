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

def test_wishbone_function_decode_json():

    e = Event('{"one": 1}')
    f = ComponentManager().getComponentByName("wishbone.function.decode.json")()
    assert f(e).get() == {"one": 1}

def test_wishbone_function_encode_json():

    e = Event({"one": 1})
    f = ComponentManager().getComponentByName("wishbone.function.encode.json")()
    assert f(e).get() == '{"one": 1}'

def test_wishbone_function_process_uppercase():

    e = Event({"case": "upper"})
    f = ComponentManager().getComponentByName("wishbone.function.process.uppercase")("@data.case", "@data.case")
    assert f(e).get() == {"case": "UPPER"}

def test_wishbone_function_process_lowercase():

    e = Event({"case": "LOWER"})
    f = ComponentManager().getComponentByName("wishbone.function.process.lowercase")("@data.case", "@data.case")
    assert f(e).get() == {"case": "lower"}

def test_wishbone_function_encode_msgpack():

    e = Event({"one": 1})
    f = ComponentManager().getComponentByName("wishbone.function.encode.msgpack")()
    assert f(e).get() == b'\x81\xa3one\x01'

def test_wishbone_function_decode_msgpack():

    e = Event(b'\x81\xa3one\x01')
    f = ComponentManager().getComponentByName("wishbone.function.decode.msgpack")()
    assert f(e).get() == {b"one": 1}
