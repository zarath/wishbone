#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  modify_append.py
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


def modifyAppendWrapper(data, destination='tags'):
    '''
    **Adds <data> to the array <destination>.**

    Adds the provided <data> string to the array <destination>.


    Parameters:

        - data(str/int/float)()
           |  data to add to <destination>
           |  can be a string or number.

        - destination(str)(tags)
           |  The destination field to append <data> to.
           |  <destination> is expected to be an array.
    '''

    def modifyAppend(event):

        nonlocal data
        if isinstance(data, (int, float, str)):
            lst = event.get(destination)
            if isinstance(lst, list):
                lst.append(data)
                event.set(lst, destination)
            else:
                raise Exception("'%s' is not an array" % (destination))
        else:
            raise Exception("'%s' is not a number or string." % (data))
        return event

    return modifyAppend
