#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_module_roundrobin.py
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
from wishbone.module.roundrobin import RoundRobin
from wishbone.actor import ActorConfig
from wishbone.utils.test import getter


def test_module_roundrobin():

    actor_config = ActorConfig('roundrobin', 100, 1, {}, "")
    roundrobin = RoundRobin(actor_config)

    roundrobin.pool.queue.inbox.disableFallThrough()

    roundrobin.pool.createQueue("one")
    roundrobin.pool.queue.one.disableFallThrough()

    roundrobin.pool.createQueue("two")
    roundrobin.pool.queue.two.disableFallThrough()

    roundrobin.start()

    event_one = Event("one")

    event_two = Event("two")

    roundrobin.pool.queue.inbox.put(event_one)
    roundrobin.pool.queue.inbox.put(event_two)

    assert getter(roundrobin.pool.queue.one).get() in ["one", "two"]
    assert getter(roundrobin.pool.queue.two).get() in ["one", "two"]

    roundrobin.stop()
