#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_module_jsondecode.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
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

from wishbone.event import Event
from wishbone.module.jsondecode import JSONDecode
from wishbone.actor import ActorConfig
from wishbone.utils.test import getter


def test_module_jsondecode_basic():

    actor_config = ActorConfig('jsondecode', 100, 1, {}, "")
    jsondecode = JSONDecode(actor_config)

    jsondecode.pool.queue.inbox.disableFallThrough()
    jsondecode.pool.queue.outbox.disableFallThrough()
    jsondecode.start()

    e = Event('["one", "two", "three"]')

    jsondecode.pool.queue.inbox.put(e)
    one = getter(jsondecode.pool.queue.outbox)
    assert one.get() == ["one", "two", "three"]

def test_module_jsondecode_strict():

    actor_config = ActorConfig('jsondecode', 100, 1, {}, "")
    jsondecode = JSONDecode(actor_config)

    jsondecode.pool.queue.inbox.disableFallThrough()
    jsondecode.pool.queue.outbox.disableFallThrough()
    jsondecode.start()

    e = Event('''{"one": "een\n"}''')

    jsondecode.pool.queue.inbox.put(e)

    try:
        getter(jsondecode.pool.queue.outbox)
    except Exception:
        assert True
    else:
        assert False

def test_module_jsondecode_nostrict():

    actor_config = ActorConfig('jsondecode', 100, 1, {}, "")
    jsondecode = JSONDecode(actor_config, strict=False)

    jsondecode.pool.queue.inbox.disableFallThrough()
    jsondecode.pool.queue.outbox.disableFallThrough()
    jsondecode.start()

    e = Event('''{"one": "een\n"}''')

    jsondecode.pool.queue.inbox.put(e)

    try:
        event = getter(jsondecode.pool.queue.outbox)
        assert event.get() == {'one': 'een\n'}
    except Exception:
        assert False
