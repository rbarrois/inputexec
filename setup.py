#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2013 Raphaël Barrois

import os
import re

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    path_components = package_components + ['__init__.py']
    with open(os.path.join(root_dir, *path_components)) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


PACKAGE = 'inputexec'


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    author="Raphaël Barrois",
    author_email="raphael.barrois+inputexec@polytechnique.org",
    description="Simple Python program to execute commands on keypress on headless systems",
    keywords=["input", "exec", "command", "evdev", "event"],
    license="BSD",
    url="https://github.com/rbarrois/inputexec",
    packages=[
        'inputexec', 'inputexec.readers',
    ],
    scripts=['bin/inputexec'],
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=[
        'evdev',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Utilities",
    ],
    test_suite='tests',
)
