#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
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

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

PROJECT = 'wishbone'
VERSION = '3.0.0'

install_requires = [
    'arrow',
    'colorama',
    'cronex',
    'gevent',
    'gipc',
    'inotify',
    'jsonschema',
    'prettytable',
    'python-daemon-3K',
    'requests',
    'pyyaml',
    'jsonschema',
    'msgpack-python',
    'easydict',
    'jinja2',
    'pygments'
]

dependency_links = [
]

try:
    with open('README.rst', 'rt') as f:
        long_description = f.read()
except IOError:
    long_description = ''


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["tests/"]
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name=PROJECT,
    version=VERSION,

    description='Build composable event pipeline servers with minimal effort.',
    long_description=long_description,

    author='Jelle Smet',
    author_email='development@smetj.net',

    url='https://github.com/smetj/wishbone',
    download_url='https://github.com/smetj/wishbone/tarball/master',
    dependency_links=dependency_links,
    classifiers=['Development Status :: 5 - Production/Stable',
                 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 ],
    extras_require={
        'testing': ['pytest'],
    },
    platforms=['Linux'],
    test_suite='tests.test_wishbone',
    cmdclass={'test': PyTest},
    scripts=[],
    provides=[],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    package_data={'': ['data/wordlist.txt', 'data/LICENCE', 'data/banner.tmpl']},
    zip_safe=False,
    entry_points={
        'console_scripts': ['wishbone = wishbone.bootstrap:main'],
        'wishbone.protocol.decode': [
            'dummy = wishbone.protocol.decode.dummy:Dummy',
            'plain = wishbone.protocol.decode.plain:Plain',
            'json = wishbone.protocol.decode.json:JSON',
            'msgpack = wishbone.protocol.decode.msgpack:MSGPack',
        ],
        'wishbone.protocol.encode': [
            'dummy = wishbone.protocol.encode.dummy:Dummy',
            'json = wishbone.protocol.encode.json:JSON',
            'msgpack = wishbone.protocol.encode.msgpack:MSGPack',
        ],
        'wishbone.module.flow': [
            'acknowledge = wishbone.module.acknowledge:Acknowledge',
            'deserialize = wishbone.module.deserialize:Deserialize',
            'fanout = wishbone.module.fanout:Fanout',
            'funnel = wishbone.module.funnel:Funnel',
            'fresh = wishbone.module.fresh:Fresh',
            'roundrobin = wishbone.module.roundrobin:RoundRobin',
            'switch = wishbone.module.switch:Switch',
            'tippingbucket = wishbone.module.tippingbucket:TippingBucket',
            'ttl = wishbone.module.ttl:TTL'
        ],
        'wishbone.module.process': [
            'modify = wishbone.module.modify:Modify',
            'template = wishbone.module.template:Template',
        ],
        'wishbone.module.input': [
            'cron =  wishbone.module.cron:Cron',
            'dictgenerator = wishbone.module.dictgenerator:DictGenerator',
            'inotify = wishbone.module.wb_inotify:WBInotify',
            'testevent = wishbone.module.testevent:TestEvent',
        ],
        'wishbone.module.output': [
            'null = wishbone.module.null:Null',
            'stdout = wishbone.module.stdout:STDOUT',
            'syslog = wishbone.module.wbsyslog:Syslog'
        ],
        'wishbone.function.module': [
            'set = wishbone.function.module.modify_set:modifySetWrapper',
            'append = wishbone.function.module.modify_append:modifyAppendWrapper',
            'uppercase = wishbone.function.module.modify_uppercase:modifyUppercaseWrapper',
            'lowercase = wishbone.function.module.modify_lowercase:modifyLowercaseWrapper',
        ],
        'wishbone.function.template': [
            'choice = wishbone.function.template.choice:Choice',
            'cycle = wishbone.function.template.cycle:Cycle',
            'epoch = wishbone.function.template.epoch:Epoch',
            'pid = wishbone.function.template.pid:PID',
            'random_bool = wishbone.function.template.random_bool:RandomBool',
            'random_integer = wishbone.function.template.random_integer:RandomInteger',
            'random_uuid = wishbone.function.template.random_uuid:RandomUUID',
            'random_word = wishbone.function.template.random_word:RandomWord',
            'strftime = wishbone.function.template.strftime:STRFTime'
        ]
    }
)
