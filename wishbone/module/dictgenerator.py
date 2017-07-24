#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       dictgenerator.py
#
#       Copyright 2017 Jelle Smet development@smetj.net
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#
from sys import version_info
from random import choice, randint
from gevent import sleep
from wishbone.actor import Actor
from wishbone.module import InputModule
import os
from wishbone.protocol.decode.dummy import Dummy


if version_info[0] == 2:
    from io import open


class DictGenerator(InputModule):

    '''**Generates random dictionaries.**

    This module allows you to generate an stream of dictionaries.

    Parameters:

        - keys(list)([])
           |  If provided, documents are created using the provided
           |  keys to which random values will be assigned.

        - randomize_keys(bool)(True)
           |  Randomizes the keys.  Otherwise keys are sequential
           |  numbers.

        - num_values(bool)(False)
           |  If true values will be numeric and randomized.

        - num_values_max(int)(1)
           |  The maximum of a value when they are numeric.

        - min_elements(int)(1)
           |  The minimum number of elements per dictionary.

        - max_elements(int)(1)
           |  The maximum number of elements per dictionary.

        - interval(int)(1)
           |  The time in seconds to sleep between each message.

    Queues:

        - outbox
           |  Outgoing messges
    '''

    def __init__(self, actor_config, keys=[], randomize_keys=True, num_values=False, num_values_min=0, num_values_max=1, min_elements=1, max_elements=1, interval=1):
        Actor.__init__(self, actor_config)

        self.wordlist = self.readWordlist()
        self._total = 0

        self.key_number = -1

        if self.kwargs.randomize_keys:
            self.generateKey = self.pickWord
        else:
            self.generateKey = self.generateKeyNumber

        if self.kwargs.num_values:
            self.generateValue = self.generateValueInteger
        else:
            self.generateValue = self.pickWord

        self.pool.createQueue("outbox")
        self.decode = Dummy().handler

    def readWordlist(self):
        with open("%s/../data/wordlist.txt" % (os.path.dirname(__file__)), encoding="latin-1") as f:
            return f.readlines()

    def preHook(self):

        if self.kwargs.keys != []:
            self.getDict = self.getDictPredefinedKeys
        else:
            self.getDict = self.getDictGeneratedKeys

        self.sendToBackground(self.generateDicts)

    def generateDicts(self):

        while self.loop():
            for payload in self.decode(self.getDict()):
                event = self.generateEvent(payload)
                self.submit(event, self.pool.queue.outbox)
                self.key_number = +1
                sleep(self.kwargs.interval)

    def getDictPredefinedKeys(self):

        d = {}
        for key in self.kwargs.keys:
            d[key] = self.pickWord()

        return d

    def getDictGeneratedKeys(self):

        d = {}
        for x in range(0, randint(self.kwargs.min_elements, self.kwargs.max_elements)):
            d[self.generateKey()] = self.generateValue()
        return d

    def pickWord(self):
        '''Returns a word as string from the wordlist.'''

        while self.loop():
            word = choice(self.wordlist).rstrip()
            try:
                return word
            except:
                pass

    def generateValueInteger(self):
        '''Returns a random number.'''
        return randint(self.kwargs.num_values_min, self.kwargs.num_values_max)

    def generateKeyNumber(self):
        '''Generates a key by incrementing integer.'''
        self.key_number += 1
        return str(self.key_number)
