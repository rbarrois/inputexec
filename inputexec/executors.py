# -*- coding: utf-8 -*-
# Copyright (c) 2013-2021 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import threading
import shlex
import subprocess
import sys

from .compat import queue


logger = logging.getLogger(__name__)


COMMANDS_SECTION = 'commands'


class BaseExecutor(object):

    def setup(self):
        """Extension point; called before the loop starts."""
        pass

    def cleanup(self):
        """Extension point; called when the loop ends, or terminated."""
        pass
    
    def handle(self, event):
        """Handle an event."""
        raise NotImplementedError()


class PrintingExecutor(BaseExecutor):
    """Simple executor that prints commands."""
    def __init__(self, out_filename, end_line='\n', **kwargs):
        self.out = None
        self.out_filename = out_filename
        self.end_line = end_line
        super(PrintingExecutor, self).__init__(**kwargs)

    def setup(self):
        """Setup: Open self.out."""
        super(PrintingExecutor, self).setup()
        if self.out_filename == '-':
            self.out = sys.stdout
        else:
            self.out = open(self.out_filename, 'w')

    def format_event(self, event):
        return event.key()

    def handle(self, event):
        self.out.write(self.format_event(event))
        self.out.write(self.end_line)
        self.out.flush()

    def cleanup(self):
        """Cleanup: close self.out."""
        if self.out is not sys.stdout:
            self.out.close()

        super(PrintingExecutor, self).cleanup()


class Task(object):
    """A simple task object.

    Attributes:
        key (str): the Event key
        event (Event): the Event
        command (str): the unparsed command to run
    """
    __slots__ = ('key', 'event', 'command')

    def __init__(self, key, event, command):
        self.key = key
        self.event = event
        self.command = command

    def __repr__(self):
        return 'Task(%r, %r, %r)' % (self.key, self.event, self.command)


class BaseTaskRunner(object):
    """Base class for task runners."""

    def execute(self, task):
        """Execute a task."""
        raise NotImplementedError()


class TaskRunner(BaseTaskRunner):
    def execute(self, task):
        logger.debug("Event %s: Running command `%s`", task.key, task.command)

        args = shlex.split(task.command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        p.communicate()

        if p.returncode != 0:
            logger.warning("Event %s: child %d (%r) exited with code %d",
                task.key, p.pid, task.command, p.returncode)


def read_command_map(filename):
    """Read a command map from a file.

    Returns:
        dict(pattern => command)
    """
    from .compat import configparser
    class TransparentConfigParser(configparser.SafeConfigParser):
        """A SafeConfigParser that doesn't alter option names."""

        def optionxform(self, option):
            return option

    cp = TransparentConfigParser()
    cp.read(filename)
    return dict(cp.items(COMMANDS_SECTION))


class BaseCommandExecutor(BaseExecutor):
    """An executor that executes commands.
    
    It will also log unmapped events (once per event)
    """

    def __init__(self, command_map, **kwargs):
        self.command_map = command_map
        self.unmapped_events = set()
        super(BaseCommandExecutor, self).__init__(**kwargs)

    def run_task(self, event):
        raise NotImplementedError()

    def _handle_not_found(self, key, event):
        if key in self.unmapped_events:
            return
        self.unmapped_events.add(key)
        logger.info("Ignoring unmapped event %s <%r>", key, event)

    def handle(self, event):
        key = event.key()
        try:
            command = self.command_map[key]
        except KeyError:
            self._handle_not_found(key, event)
        else:
            task = Task(key, event, command)
            self.run_task(task)


class BlockingExcutor(BaseCommandExecutor):
    def __init__(self, **kwargs):
        super(BlockingExcutor, self).__init__(**kwargs)
        self.runner = TaskRunner()

    def run_task(self, task):
        self.runner.execute(task)


class AsyncWorker(threading.Thread):
    def __init__(self, queue, stopped, runner_kwargs=None, **kwargs):
        self.queue = queue
        self.stopped = stopped
        self.runner = TaskRunner(**(runner_kwargs or {}))
        super(AsyncWorker, self).__init__(**kwargs)

    def run(self):
        while True:
            if self.stopped.is_set():
                # Manager ordered us to stop
                break
            task = self.queue.get()

            try:
                self.runner.execute(task)

            except Exception as e:  # pylint: disable=W0703
                logger.exception("Error while running task %r: %s", task, e)

            finally:
                self.queue.task_done()


class AsyncExecutor(BaseCommandExecutor):
    def __init__(self, jobs=1, **kwargs):
        super(AsyncExecutor, self).__init__(**kwargs)
        self.nb_jobs = jobs
        self.queue = queue.Queue()
        self.stopped = threading.Event()

    def setup(self):
        """Setup: start worker threads."""
        for _i in range(self.nb_jobs):
            thread = AsyncWorker(self.queue, self.stopped)
            thread.daemon = True
            thread.start()

    def run_task(self, task):
        self.queue.put(task)

    def cleanup(self):
        """Cleanup: Set 'stop now' signal and wait."""
        self.stopped.set()
        self.queue.join()
