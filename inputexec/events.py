# -*- coding: utf-8 -*-
# Copyright (c) 2013-2021 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals


class Event(object):
    """A simple event.

    Could be anything from a key press to a joystick move to a line of text.
    
    Attributes:
        kind (str): the event kind; e.g keypress/keyrelease/abs/sync/...
        symbol (str): the event symbol (KEY_EQUAL, ...)
        code (int): the code mapped to the symbol
        value (int): the event 'value', depending on the kind.
    """

    __slots__ = ('kind', 'code', 'symbol', 'value')

    def __init__(self, kind, code=0, symbol='', value=0):
        self.kind = kind
        self.code = code
        self.symbol = symbol
        self.value = value

    def key(self, pattern='{kind}.{symbol}'):
        return pattern.format(
            kind=self.kind,
            code=self.code,
            symbol=self.symbol,
            value=self.value,
        )

    def __repr__(self):
        return 'Event(%r, %r, %r, %r)' % (
            self.kind,
            self.code,
            self.symbol,
            self.value,
        )

