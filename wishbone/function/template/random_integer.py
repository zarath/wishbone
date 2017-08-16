#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  random_integer.py
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

from wishbone.function.template import TemplateFunction
from random import randint


class RandomInteger(TemplateFunction):
    '''**Returns a random integer.**

    Returns a random integer between <min> and <max>.

    - Parameters to initialize the function:

        - minimum(int)(0): The minimum value
        - maximum(int)(0): The maximum value

    - Parameters to call the function:

        None
    '''

    def __init__(self, minimum=0, maximum=0):

        self.minimum = minimum
        self.maximum = maximum

    def lookup(self):

        return randint(self.minimum, self.maximum)
