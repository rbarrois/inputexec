# -*- coding: utf-8 -*-
# Copyright (c) 2013-2021 Raphaël Barrois
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


def unescape(value):
    """Un-escape a supported value."""
    ESCAPES = {
        r'\0': '\0',  # Null byte
        r'\\': '\\',  # Escaping the escape character
        r'\a': '\a',  # Bell
        r'\b': '\b',  # Backspace
        r'\f': '\f',  # Form feed
        r'\n': '\n',  # Newline
        r'\r': '\r',  # Carriage return
        r'\t': '\t',  # Horizontal tab
        r'\v': '\v',  # Vertical tab
    }
    for source, dest in ESCAPES.items():
        value = value.replace(source, dest)
    return value


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
            Arg(
                '--pattern',
                help="Formatting pattern. Valid patterns are: {code}, {kind}, {symbol}, {value}.",
                default='{kind}.{symbol}',
            ),
            Arg(
                '--endline',
                help="End of line substring. Handles standard ASCII escapes: "
                    "\\0, \\\\, \\a, \\b, \\f, \\n, \\r, \\t, \\v",
                default='\\n',
            ),
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
        if src != '-':
            is_dir = os.path.isdir(src)
            if is_dir or self._is_evdev(src):
                try:
                    from .readers import evdev as evdev_readers
                except ImportError:
                    logger.error("Unable to import python-evdev, but targeting /dev/input device(s).")
                    raise

                event_filter = evdev_readers.Filter(args.filter_kinds.split(','))
                exclusive = args.source_mode == 'exclusive'

                if is_dir:
                    return evdev_readers.EvdevDirReader(src,
                        exclusive=exclusive,
                        filter=event_filter,
                    )
                else:
                    return evdev_readers.EvdevReader(src,
                        exclusive=exclusive,
                        filter=event_filter,
                    )

        return line_readers.LineReader(src,
            pattern=args.format_pattern,
            end_line=unescape(args.format_endline),
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
                end_line=unescape(args.format_endline),
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
