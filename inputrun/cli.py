import argparse
import sys

from . import __version__
from . import readers
from . import printers
from . import runners


class Setup(object):

    def make_argparser(self):
        parser = argparse.ArgumentParser(description="Read events from an input device")

        dev_group = parser.add_argument_group("Device")
        dev_group.add_argument('device', help="The device to read from (e.g /dev/input/event0)")
        dev_group.add_argument('--mode', choices=['exclusive', 'shared'], default='exclusive',
            help="Get shared/exclusive hold of the input device")

        fmt_group = parser.add_argument_group("Formatting")
        fmt_group.add_argument('--pattern', help="Formatting pattern", default='{symbol}')

        output_group = parser.add_argument_group("Output")
        output_group.add_argument('--out', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
            help="The file to write to (default: stdout)")

        #filter_group = parser.add_argument_group("Filtering events")

        parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)

        return parser

    def make_reader(self, args):
        return readers.Reader(args.device)

    def make_formatter(self, args):
        if args.out:
            return commands.PrintingExecutor(args.out)
        else:
            return commands.CommandExecutor(args.actions)

    def make_runner(self, args):
        reader = self.make_reader(args)
        formatter = self.make_formatter(args)

        return runners.Runner(reader, formatter, args.out)

    def run(self, argv):
        argparser = self.make_argparser()
        args = argparser.parse_args()

        runner = self.make_runner(args)
        try:
            runner.run(args.mode=='exclusive', close_output=True)
        except KeyboardInterrupt:
            pass


def main(argv):
    setup = Setup()
    setup.run(argv)
