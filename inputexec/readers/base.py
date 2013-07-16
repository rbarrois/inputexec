# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals


class BaseReader(object):
    def setup(self):
        pass

    def read(self):
        """Read events.

        Yield:
            events.Event
        """
        raise NotImplementedError()

    def cleanup(self):
        pass
