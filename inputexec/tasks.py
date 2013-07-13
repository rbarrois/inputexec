# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from . import errors


class Task(object):
    def __init__(self, event, action):
        self.event = event
        self.action = action

    def __repr__(self):
        return "<Task: %s %s => %r>" % (self.event.kind, self.event.symbol, self.action)
