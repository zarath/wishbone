#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_function.py
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

from plain import Plain



def main():
    stream = [
        b"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxzxxxxxxxxxx",
        b"xxxxxxxxxxxxxxxxxxxxzxxxxxxxxxxxxzxxxxxxxxxxxx",
        b"xxxxxxxxxxxxxxxxxxxxzxxxxxxxxxxxxzxxxxxxxxxxxx",
        b"xxxxxxxxxxxxxxxxxxxxzxxxxxxxxxxxxzxxxxxxxxxxxx",
        b"xxxxxzxxxxzxxxxxzxxxxxxxxxvvvvxxxxxzxxxxxxxxxx",
        None
    ]

    # for s in stream:
    #     for item in Plain(delimiter="z").decode(s):
    #         print(item)

    p = Plain(delimiter=None)
    for s in stream:
        for item in p.decode(s):
            print(item)


if __name__ == "__main__":
    main()
