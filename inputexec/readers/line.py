# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

"""Reads inputs from a line-based file."""

import re
import sys

from . import base
from .. import events


class LineReader(base.BaseReader):
    """A simple line reader.

    Attributes:
        in_filename (str): path to the file to read from ('-' for stdin)
        in_file (file): opened file to read from
        pattern (str): pattern for incoming lines, with placeholders
        end_line (str): end of input lines
        regexp (re.RegexObject): regexp computed from the pattern
    """

    def __init__(self, in_filename, pattern='{kind}.{symbol}', end_line='\n',
            **kwargs):
        super(LineReader, self).__init__(**kwargs)
        self.in_filename = in_filename
        self.in_file = None
        self.end_line = end_line
        self.pattern = pattern
        self.regexp = self._convert_pattern(pattern)

    def _convert_pattern(self, pattern):
        fields = {
            'kind': r'(?P<kind>\w+)',
            'symbol': r'(?P<symbol>\w+)',
            'code': r'(?P<code>\d+)',
            'value': r'(?P<value>\d+)',
        }
        pattern = re.escape(pattern)

        for field, regexp in fields.items():
            subpattern = r'\{%s\}' % field
            pattern = pattern.replace(subpattern, regexp)
        return re.compile(pattern)

    def setup(self):
        """Setup: Open the input file."""
        super(LineReader, self).setup()
        if self.in_filename == '-':
            self.in_file = sys.stdin
        else:
            self.in_file = open(self.in_filename, 'r')

    def make_event(self, line):
        """Turn a line into an event.

        Uses the :attr:`regexp` to match the line, with a fallback to
        "line.%(line)s"
        """
        match = self.regexp.match(line)
        if match:
            fields = match.groupdict()
        else:
            fields = {
                'kind': 'line',
                'symbol': line,
            }
        return events.Event(**fields)

    def read(self):
        for line in self.in_file:
            # Don't 
            yield self.make_event(line.rstrip(self.end_line))

    def cleanup(self):
        """Cleanup: Close the input file."""
        if self.in_filename != '-':
            self.in_file.close()

        super(LineReader, self).cleanup()
