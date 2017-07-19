#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  load_data.py
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


import os
import json
import yaml
from gevent.lock import Semaphore
from jsonschema import validate
from wishbone.error import InvalidData


class StructuredDataFile():

    '''
    Loads and optionally validates structured data from disk.

    The module loads data from disk and optionally validates the data against
    the provided schema.  The datastructure can be JSON and/or YAML.

    Attributes:
        default (obj): The default value when no file content has loaded yet.
        schema (str): The JSONschema to validate the loaded data against.
        expect_json (bool): When True, the data structure can be JSON
        expect_yaml (bool): When True, the data structure can be YAML.
        content (dict): The loaded configurations.  Absolute paths are dict keys.
    '''

    def __init__(self, default=None, schema=None, expect_json=True, expect_yaml=True):
        '''
        Args:
            default (obj): A default value to return when no file content has loaded yet.
            schema (str): The JSONschema to validate the loaded data against.
            expect_json (bool): When True, the data structure can be JSON
            expect_yaml (bool): When True, the data structure can be YAML.
        '''

        self.default = default
        self.schema = schema
        self.expect_json = expect_json
        self.expect_yaml = expect_yaml
        self.content = None
        self.lock = Semaphore()
        self.current_filename = None

    def delete(self, path):
        '''Deletes the file content from the object'''

        with self.lock:
            self.content = None

    def dump(self):
        '''Dumps the complete content'''

        with self.lock:
            if self.content is None:
                return self.default
            else:
                return self.content

    def get(self, path):
        '''Returns the cached content of the file.  If the file isn't loaded yet, it
        tries to do that.'''

        with self.lock:
            if self.content is None or os.path.abspath(path) != self.current_filename:
                return self.__load(path)
            else:
                return self.content

    def load(self, path):
        '''Loads the file into the module and validates the content when required.'''

        with self.lock:
            return self.__load(os.path.abspath(path))

    def __load(self, path):

        if os.path.exists(path) and os.access(path, os.R_OK):
            if os.path.isfile(path):
                self.__readFile(path)
                if self.schema is not None:
                    try:
                        validate(self.content, self.schema)
                    except Exception as err:
                        # error = str(err)
                        # error = error.replace("\n", " ->")
                        # raise InvalidData(" ".join(str(error).split()))
                        raise InvalidData(err.message)
            else:
                raise Exception("'%s' does not appear to be a regular file.")
        else:
            raise Exception("File '%s' does not exist or is not accessible." % (path))

        return self.content

    def __readFile(self, path):

        with open(path) as f:
            errors = []

            if self.expect_json:
                try:
                    self.__readJSON(f)
                except Exception as err:
                    errors.append("JSON: %s" % str(err))
                else:
                    return

            if self.expect_yaml:
                try:
                    self.__readYAML(f)
                except Exception as err:
                    errors.append("YAML: %s" % str(err))
                else:
                    return

            if len(errors) > 0:
                raise Exception("Could not load file '%s'.  Reason: '%s'" % (path, ",".join(errors)))

    def __readJSON(self, f):
        f.seek(0)
        data = json.load(f)
        self.content = data
        return True

    def __readYAML(self, f):
        f.seek(0)
        data = yaml.load(f)
        self.content = data
        return True
