# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import logging.handlers
import os
import sys

from . import __version__
from .config import Arg, Group, UnifiedParser

from .readers import line as line_readers
from . import executors
from . import loop

logger = logging.getLogger(__name__)


class Setup(object):
    description = "Read events from an input device/stream, and run related commands."
    options = [
        Group('', "", [
            Arg('--traceback', help="Include full stack trace on exception", action='store_true'),
        ]),

        Group('source', "Source", [
            Arg('--file', help="The source to read from (e.g /dev/input/event0)", default='-'),
            Arg('--mode', choices=['exclusive', 'shared'], default='exclusive',
                help="Get shared/exclusive hold of the input device (evdev only)"),
        ]),

        Group('format', "Formatting", [
            Arg('--pattern', help="Formatting pattern", default='{kind}.{symbol}'),
            Arg('--endline', help="End of line substring", default='\\n'),
        ]),

        Group('action', "Action", [
            Arg('--mode', choices=['run_async', 'run_sync', 'print'],
                default='print', help="Action to perform on events"),
            Arg('--jobs', type=int, default=1, help="Number of jobs to run"),
            Arg('--commands',
                help=("Read input/command mappings from the ACTION_COMMANDS file, "
                "section [%s]" % executors.COMMANDS_SECTION)),
        ]),

        Group('filter', "Filtering events", [
            Arg('--kinds', help="Comma-separated list of event kinds to keep", default='keypress'),
        ]),

        Group('logging', "Logging", [
            Arg('--target', help="Logging target", choices=['null', 'file', 'stderr', 'syslog'],
                default='stderr'),
            Arg('--file', help="For 'file' target, write logs to FILE"),
            Arg('--level', help="Logging level", choices=['debug', 'info', 'warning', 'error'],
                default='warning'),
        ]),
    ]

    def error(self, message, code=1):
        sys.stderr.write("Error: %s\n" % message)
        sys.exit(code)

    def _is_evdev(self, path):
        LINUX_INPUT_DEV_MAJOR = 13
        st = os.stat(path)
        return os.major(getattr(st, 'st_rdev', 0)) == LINUX_INPUT_DEV_MAJOR

    def setup_logging(self, args):
        if args.logging_target == 'syslog':
            handler = logging.handlers.SysLogHandler()
        elif args.logging_target == 'stderr':
            handler = logging.StreamHandler()
        elif args.logging_target == 'file':
            if not args.logging_file:
                self.error("--logging-file is required for --logging-target=file")
            handler = logging.FileHandler(args.logging_file)
        else:
            handler = logging.NullHandler()

        formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)

        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
        }
        root_logger = logging.getLogger()
        root_logger.setLevel(level_map[args.logging_level])
        root_logger.addHandler(handler)

    def make_reader(self, args):
        src = args.source_file
        if src == '-':
            evdev = False
        else:
            evdev = self._is_evdev(src)

        if evdev:
            try:
                from .readers import evdev as evdev_readers
            except ImportError:
                logger.error("Unable to import python-evdev, but targeting a /dev/input device.")
                raise

            event_filter = evdev_readers.Filter(args.filter_kinds.split(','))
            exclusive = args.source_mode == 'exclusive'
            evdev_device = evdev_readers.open_device(src)
            return evdev_readers.EvdevReader(evdev_device,
                exclusive=exclusive,
                filter=event_filter,
            )

        else:
            return line_readers.LineReader(src,
                pattern=args.format_pattern,
                end_line=args.format_endline.decode('string_escape'),
            )

    def make_executor(self, args):
        if args.action_mode in ('run_sync', 'run_async'):
            commands_file = args.action_commands or args.config
            if not commands_file:
                self.error(
                    "When using run_sync/run_async executors, at least "
                    "of --config or --action-commands must be filled.")
            commands = executors.read_command_map(commands_file)

        if args.action_mode == 'run_async':
            return executors.AsyncExecutor(jobs=args.action_jobs, command_map=commands)
        elif args.action_mode == 'run_sync':
            return executors.BlockingExcutor(command_map=commands)
        else:
            return executors.PrintingExecutor('-',
                end_line=args.format_endline.decode('string_escape'),
            )

    def make_runner(self, args):
        self.setup_logging(args)
        reader = self.make_reader(args)
        executor = self.make_executor(args)

        return loop.Loop(reader, executor)

    def run(self, argv):
        config = UnifiedParser(self.options,
            with_dump_config=True,
            description=self.description,
            version=__version__,
        )
        args = config.parse(argv[1:])

        runner = self.make_runner(args)
        logger.info("Starting loop.")
        try:
            runner.loop()
        except Exception as e:  # pylint: disable=W0703
            if args.traceback:
                raise
            else:
                self.error('%s: %s' % (e.__class__.__name__, e), 2)


def main(argv):
    setup = Setup()
    setup.run(argv)
