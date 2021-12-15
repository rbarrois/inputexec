# -*- coding: utf-8 -*-
# Copyright (c) 2013-2021 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)


class Loop(object):
    def __init__(self, reader, executor):
        self.reader = reader
        self.executor = executor

    def loop(self):
        self.reader.setup()
        self.executor.setup()

        count = 0
        try:
            for event in self.reader.read():
                self.executor.handle(event)
                count += 1

        except KeyboardInterrupt:
            # We're a command-line program, avoid tracebacks.
            pass

        finally:
            self.executor.cleanup()
            self.reader.cleanup()

        logger.info("Handled %d events.", count)
