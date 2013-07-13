# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import unicode_literals


class BaseExecutor(object):
    def handle(self, event):
        """Handle an event."""
        raise NotImplementedError()


class PrintingExecutor(BaseExecutor):
    """Simple executor that prints commands."""
    def __init__(self, out, end_line='\n', **kwargs):
        self.out = out
        self.end_line = end_line
        super(PrintingExecutor, self).__init__(**kwargs)

    def handle(self, event):
        self.out.write(event.keycode)
        self.out.write(self.end_line)
        self.out.flush()


class RunningExecutor(BaseExecutor):

    def handle(self, event):
        pass
