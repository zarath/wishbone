#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_protocol_decode_json.py
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


from wishbone.protocol.decode.json import JSON

class ReadlinesMock():

    data = [
        b'{"one":',
        b'1}'
    ]

    def readlines(self):

        return self.data

def test_protocol_decode_json_basic():

    m = JSON()
    for item in m.handler(b'{"one": 1}'):
        assert item == {"one": 1}

def test_protocol_decode_json_unicode():

    m = JSON()
    for item in m.handler(b'{"one": \xce\xb1"}'):
        assert item == {"one": u"α"}
        assert isinstance(item["one"], unicode)

def test_protocol_decode_json_readlines():

    j = JSON()
    reader = ReadlinesMock()
    for item in j.handler(reader):
        assert item == {"one": 1}
