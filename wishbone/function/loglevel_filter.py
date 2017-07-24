#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  loglevel_filter.py
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


def logLevelFilter(source='data.level', max_loglevel=6):

    '''
    **Drops the log event if max_loglevel has been exceeded.**

    Validates whether `data.level` is smaller or equal to max_loglevel.

    Parameters:

        - source(str)('data.level')
            |  The field containing the loglevel

        - max_loglevel(int)(6)
            |  The maximum allowed loglevel
    '''

    def processLogLevelFilter(event):
        if event.get(source) <= max_loglevel:
            return event
        else:
            return None

    return processLogLevelFilter
