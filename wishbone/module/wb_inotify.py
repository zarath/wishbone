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

# I know no other working way to actually monkey patch select
# when inotify is imported.
# If you know another way, please consider submitting a
# patch or merge request
# todo(smetj): Fix dirty monkey patch of inotify select
import sys
from gevent import monkey; monkey.patch_all()
from gevent import select
sys.modules["select"] = sys.modules["gevent.select"]
sys.modules["select"].epoll = sys.modules["select"].poll

from inotify.adapters import Inotify
from inotify.adapters import _LOGGER
from inotify import constants

from wishbone.event import Event
from gevent import sleep
import os
import fnmatch


class WBInotify(Actor):

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

        - initial_listing(bool)(True)

           |  When True, generates for each defined path an event.  This is
           |  useful to initially give depending modules the filenames they
           |  need to function.

        - glob_pattern(str)(*)

           |

        - paths(dict)({"/tmp": ["IN_CREATE"]})

           |  A dict of paths with a list of inotify events to monitor.  When
           |  the list is empty no filtering is done and results into all
           |  inotify events going through.


    Queues:

        - outbox
           |  Outgoing notify events.

    '''

    def __init__(self, actor_config, initial_listing=True, glob_pattern="*", paths={"/tmp": ["IN_CREATE"]}):
        Actor.__init__(self, actor_config)
        self.pool.createQueue("outbox")

    def preHook(self):

        for path, event_types in self.kwargs.paths.items():
            for event_type in event_types:
                if event_type not in constants.__dict__:
                    raise Exception("Inotify event type '%s' defined for path '%s' is not valid." % (event_type, path))

        for path, inotify_types in self.kwargs.paths.items():
            self.sendToBackground(self.monitor, path, inotify_types)

    def monitor(self, path, inotify_types):

        while self.loop():
            if os.path.exists(path) and os.access(path, os.R_OK):
                file_exists = True
                if self.kwargs.initial_listing:
                    if os.path.isdir(path):
                        all_files = [os.path.abspath("%s/%s" % (path, name)) for name in os.listdir(path) if os.path.isfile("%s/%s" % (path, name))]
                    else:
                        all_files = [os.path.abspath(path)]

                    for f in all_files:
                        if fnmatch.fnmatch(f, self.kwargs.glob_pattern):
                            self.pool.queue.outbox.put(
                                Event(
                                    {"path": f, "inotify_type": "WISHBONE_INIT"}
                                )
                            )
                all_types = ', '.join(inotify_types)
                if all_types == '':
                    all_types = "ALL"
                self.logging.info("Started to monitor path '%s' for '%s' inotify events." % (os.path.abspath(path), all_types))
                try:
                    i = Inotify(block_duration_s=1000)
                    i.add_watch(path)
                    while file_exists and self.loop():
                        for event in i.event_gen():
                            if event is not None:
                                for inotify_type in event[1]:
                                    if inotify_type in inotify_types or inotify_types == []:
                                        abs_path = "%s/%s" % (event[2], event[3])
                                        if fnmatch.fnmatch(abs_path, self.kwargs.glob_pattern):
                                            e = Event(
                                                    {"path": abs_path.rstrip('/'), "inotify_type": inotify_type}
                                                )
                                            self.pool.queue.outbox.put(e)
                                    if inotify_type == "IN_DELETE_SELF":
                                        file_exists = False
                                        break
                            else:
                                sleep(1)
                                break
                except Exception as err:
                    self.logging.critical('Failed to initialize inotify monitor. This needs immediate attention. Reason: %s' % err)
                    sleep(1)
            else:
                self.logging.warning("The defined path '%s' does not exist or is not readable. Will sleep for 5 seconds and try again." % (path))
                sleep(5)
