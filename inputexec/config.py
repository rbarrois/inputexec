# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals


import argparse
import sys

from .compat import configparser

class Group(object):
    """A group of options/args.

    Maps to a section for configparser.

    Attributes:
        name (str): short name for the section.
            Used as section name in configparser and prefix in argparse.
        title (str): verbose name for group header in argparse
        args (Arg list): Arguments within the group
    """
    def __init__(self, name, title, args):
        self.name = name
        self.title = title
        self.args = args

    def make_argparse_group(self, parser):
        """Create and attache an argparse-style group to its parser."""
        if self.name:
            group = parser.add_argument_group(self.title)
        else:
            group = parser

        for arg in self.args:
            arg.add_to_argparse_group(self.name, group)

    def ini_lines(self):
        """Generate example configuration lines."""
        if self.name:
            yield '## %s' % self.title
            yield '[%s]' % self.name
        else:
            yield '[%s]' % configparser.DEFAULTSECT

        for arg in self.args:
            for line in arg.ini_lines(self.name):
                yield line

    def fill_argparse_defaults(self, parser, parsed_file):
        for arg in self.args:
            if self.name:
                argparse_option_name = '%s_%s' % (self.name, arg.main_option)
                section_name = self.name
            else:
                argparse_option_name = arg.main_option
                section_name = configparser.DEFAULTSECT

            try:
                value = parsed_file.get(section_name, arg.main_option)
            except (configparser.NoSectionError, configparser.NoOptionError):
                continue

            parser.set_defaults(**{argparse_option_name: value})


class Arg(object):
    """A single argument/option.

    Attributes:
        options (str list): command line flags
        main_option (str): the main option, without leading dashed
        default (obj): the default value
        help (str): the help text
        extra (dict): additional keywords for argparse
    """
    def __init__(self, *options, **kwargs):
        if 'dest' in kwargs:
            raise ValueError("The 'dest' kwarg is not allowed.")

        self.options = options
        self.main_option = options[0].lstrip('-')
        self.default = kwargs.pop('default', '')
        self.help = kwargs.pop('help', '')
        self.extra = kwargs

    def prefixed_options(self, prefix):
        """Retrieve the list of prefixed options, using a given prefix."""
        for option in self.options:
            if option.startswith('--'):
                yield '--%s-%s' % (prefix, option[2:])
            elif option.startswith('-'):
                # Short option
                yield option
            else:
                # Positional argument
                yield '%s_%s' % (prefix, option)

    def config_help_line(self, prefix):
        """Build a documentation line for configuration files."""
        options_str = ' / '.join(self.prefixed_options(prefix))
        if self.help:
            return '; %s : %s' % (options_str, self.help)
        else:
            return '; %s' % options_str

    def config_line(self):
        """Build an example key/value pair for the configuration file."""
        return '%s = %s' % (self.main_option.lstrip('-'), self.default)

    def ini_lines(self, prefix):
        yield self.config_help_line(prefix)
        if self.extra.get('choices'):
            yield '; Options: %s' % ', '.join(sorted(self.extra['choices']))
        yield self.config_line()

    def add_to_argparse_group(self, prefix, group):
        if prefix:
            options = list(self.prefixed_options(prefix))
        else:
            options = list(self.options)
        group.add_argument(*options,
            help=self.help,
            default=self.default,
            **self.extra)


class Options(object):
    def __init__(self, groups):
        self.groups = groups


class DumpConfigAction(argparse.Action):
    def __init__(self, option_strings, unified_parser,
            dest=argparse.SUPPRESS, default=False, required=False, help='',
            **kwargs):  # pylint: disable=W0622
        super(DumpConfigAction, self).__init__(option_strings, dest=dest,
                default=default, required=required, help=help, **kwargs)
        self.unified_parser = unified_parser

    def __call__(self, parser, namespace, values, option_string=None):
        cfg = self.unified_parser.make_ini(progname=parser.prog)
        sys.stdout.write(cfg)
        parser.exit(0)


class UnifiedParser(object):
    """A global configuration parser.

    Attributes:
        options (Options): List of options
        with_dump_config (bool): whether to add the --dump-config option
        description (str): optional description for the program parser
        version (str): optional version number
    """

    def __init__(self, options, with_dump_config=True,
            description='', version='', **kwargs):
        self.options = options
        self.with_dump_config = with_dump_config
        self.description = description
        self.version = version
        super(UnifiedParser, self).__init__(**kwargs)

    def _make_ini_lines(self, progname=''):
        if progname:
            yield '; Configuration file for %s' % progname
            yield ''

        for group in self.options:
            for line in group.ini_lines():
                yield line
            yield ''

    def make_ini(self, progname=''):
        return '\n'.join(self._make_ini_lines(progname))

    def fill_argparse_parser(self, parser):
        for group in self.options:
            group.make_argparse_group(parser)

    def fill_argparse_defaults(self, parser, parsed_file):

        for group in self.options:
            group.fill_argparse_defaults(parser, parsed_file)

    def make_parser(self, full=True):
        """Prepare the parser.

        Args:
            full (bool): whether to include all options, or only --config.
        """
        parser = argparse.ArgumentParser(
            description=self.description,
            add_help=full,
        )

        parser.add_argument('--config', action='append',
            help="Read additional configuration options from these files")

        if not full:
            return parser

        self.fill_argparse_parser(parser)

        if self.with_dump_config:
            parser.add_argument('--dump-config', action=DumpConfigAction,
                unified_parser=self, nargs=0,
                help="Display a default config file.")

        if self.version:
            parser.add_argument('-V', '--version', action='version',
                version='%(prog)s ' + self.version)

        return parser

    def parse(self, argv):
        """Parse an argument vector.

        This should be sys.argv[1:].
        """
        # First, get the --config option.
        simple_parser = self.make_parser(full=False)
        simple_args, _extra = simple_parser.parse_known_args(argv)
        cp = configparser.SafeConfigParser()
        if simple_args.config:
            cp.read(simple_args.config)

        # Now, generate the full, exhaustive parser
        full_parser = self.make_parser(full=True)
        self.fill_argparse_defaults(full_parser, cp)

        return full_parser.parse_args(argv)
