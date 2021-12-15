# -*- coding: utf-8 -*-
# Copyright (c) 2013-2021 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.


# pylint: disable=F0401,W0611

import sys


if sys.version_info[0] == 2:
    # Python 2
    import ConfigParser as configparser
    import Queue as queue

else:
    import configparser
    import queue
