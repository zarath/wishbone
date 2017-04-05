#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  plain.py
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


from wishbone.protocol import Decode
from wishbone.error import ProtocolError
from io import BytesIO
from msgpack import Unpacker


class EndOfStream(Exception):
    pass


class MSGPack(Decode):

    '''**Decodes MSGPack format into .**

    Converts bytestring into unicode using the defined charset.

    Parameters:

        - charset(string)("utf-8")
           |  The charset to use to decode the bytestring data.

        - buffer_size(int)(4096)
           |  The max amount of bytes allowed to read for 1 event

    '''

    def __init__(self, charset="utf-8", buffer_size=4096):

        self.charset = charset
        self.buffer_size = buffer_size
        self.__leftover = ""
        self.buffer = BytesIO()
        self.__buffer_size = 0

        self.unpacker = Unpacker(buf)

    def decode(self, data):

        if data is None or data == b'':
            self.buffer.seek(0)
            try:
                yield loads(self.buffer.getvalue().decode(self.charset))
            except Exception as err:
                raise ProtocolError("ProtcolError: %s" % (err))
        else:
            self.__buffer_size += self.buffer.write(data)
            if self.__buffer_size > self.buffer_size:
                raise Exception("Buffer exceeded.")
            return []
