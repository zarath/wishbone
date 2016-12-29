#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  wb_inotify.py
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

from wishbone import Actor
from gevent import monkey; monkey.patch_all()
from inotify.adapters import Inotify as InotifyLib
from inotify.adapters import _LOGGER
from wishbone.event import Event
import select
import inotify.adapters
from gevent import sleep
import os

class GeventInotify(InotifyLib):

    def __init__(self, paths=[], block_duration_s=10000):
        super(GeventInotify, self).__init__()
        self.__block_duration = block_duration_s
        self.__watches = {}
        self.__watches_r = {}
        self.__buffer = b''

        self.__inotify_fd = inotify.calls.inotify_init()
        _LOGGER.debug("Inotify handle is (%d).", self.__inotify_fd)

        # self.__epoll = select.epoll()
        self.__epoll = select.poll()
        self.__epoll.register(self.__inotify_fd, select.POLLIN)

        for path in paths:
            self.add_watch(path)

    def event_gen(self):
        while True:
            # block_duration_s = self.__get_block_duration

            # Poll, but manage signal-related errors.

            try:
                events = self._Inotify__epoll.poll()
            except IOError as e:
                if e.errno != EINTR:
                    raise
                continue

            # Process events.

            for fd, event_type in events:
                # (fd) looks to always match the inotify FD.

                for (header, type_names, path, filename) \
                        in self._Inotify__handle_inotify_event(fd, event_type):
                    yield (header, type_names, path, filename)

class Inotify(Actor):

    '''**Monitors one or more paths for inotify events.**

    Monitors one or more paths for the defined inotify events.

    Inotify events can have following values:

        - IN_ACCESS
        - IN_ALL_EVENTS
        - IN_ATTRIB
        - IN_CLOEXEC
        - IN_CLOSE
        - IN_CLOSE_NOWRITE
        - IN_CLOSE_WRITE
        - IN_CREATE
        - IN_DELETE
        - IN_DELETE_SELF
        - IN_DONT_FOLLOW
        - IN_IGNORED
        - IN_ISDIR
        - IN_MASK_ADD
        - IN_MODIFY
        - IN_MOVE
        - IN_MOVED_FROM
        - IN_MOVED_TO
        - IN_MOVE_SELF
        - IN_NONBLOCK
        - IN_ONESHOT
        - IN_ONLYDIR
        - IN_OPEN
        - IN_Q_OVERFLOW
        - IN_UNMOUNT

    Parameters:

        - paths(dict)({"/tmp": ["IN_CREATE"]})

           |  A dict of paths with a list of inotify events to monitor.  When
           |  the list is empty no filtering is done and results into all
           |  inotify events going through.


    Queues:

        - outbox
           |  Outgoing notify events.

    '''

    def __init__(self, actor_config, paths={"/tmp": ["IN_CREATE"]}):
        Actor.__init__(self, actor_config)
        self.pool.createQueue("outbox")

    def preHook(self):

        for path, inotify_types in self.kwargs.paths.items():
            self.sendToBackground(self.monitor, path, inotify_types)

    def monitor(self, path, inotify_types):

        while self.loop():
            if os.path.exists(path) and os.access(path, os.R_OK):
                file_exists = True
                self.logging.info("Started to monitor path '%s' for '%s' events." % (path, ','.join(inotify_types)))
                try:
                    i = GeventInotify(block_duration_s=1000)
                    i.add_watch(path)
                    while file_exists and self.loop():
                        for event in i.event_gen():
                            for inotify_type in event[1]:
                                if inotify_type in inotify_types or inotify_types == []:
                                    e = Event(inotify_type)
                                    abs_path = "%s/%s" % (event[2], event[3])
                                    e.set(abs_path.rstrip('/'), key="@tmp.%s.path" % (self.name))
                                    self.pool.queue.outbox.put(e)
                            if inotify_type == "IN_DELETE_SELF":
                                file_exists = False
                                break
                except Exception as err:
                    self.logging.critical('Failed to initialize inotify monitor. This needs immediate attention. Reason: %s' % err)
                    sleep(1)
            else:
                self.logging.warning("The defined path '%s' does not exist or is not readable. Will sleep for 5 seconds and try again." % (path))
                sleep(5)
