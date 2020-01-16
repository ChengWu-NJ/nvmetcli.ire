#! /usr/bin/python3
'''
This file is part of ConfigShell.
Copyright (c) 2011-2013 by Datera, Inc

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
'''

from setuptools import setup

setup(
    name = 'nvmetcli.ire',
    version = 0.7,
    description = 'NVMe target configuration tool. A branch with adding nguid_bydev of git://git.infradead.org/users/hch/nvmetcli.git commit:0a6b088d tag:v0.7',
    license = 'Apache 2.0',
    test_suite='nose2.collector.collector',
    packages = ['nvmet'],
    scripts=['nvmetcli', 'nguidwithdev.py', 'ecode_uuid.py'],
    install_requires=['configshell-fb>=1.1.25', 'pyparsing>=2.1.10']
    )
