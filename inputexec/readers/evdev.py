# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

"""Reads inputs from an evdev device."""

import evdev
import logging
import select

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import base
from .. import events

logger = logging.getLogger(__name__)


class UnhandledEvent(Exception):
    pass


EVENT_SYNC = 'sync'
EVENT_KEYPRESS = 'keypress'
EVENT_KEYHOLD = 'keyhold'
EVENT_KEYRELEASE = 'keyrelease'
EVENT_RELMOVE = 'relmove'
EVENT_ABSMOVE = 'absmove'


class Filter(object):
    """Filters events."""
    def __init__(self, kinds=(EVENT_KEYPRESS,), **kwargs):
        super(Filter, self).__init__(**kwargs)
        self.kinds = kinds

    def should_send(self, event):
        """Whether an Event should be handled."""
        return event.kind in self.kinds


def _map_event(evdev_event):

    code = evdev_event.code

    if evdev_event.type == evdev.events.EV_SYN:
        kind = EVENT_SYNC
        symbol = evdev.ecodes.SYN[evdev_event.code]

    elif evdev_event.type == evdev.events.EV_REL:
        kind = EVENT_RELMOVE
        symbol = evdev.ecodes.REL[evdev_event.code]

    elif evdev_event.type == evdev.events.EV_ABS:
        kind = EVENT_ABSMOVE
        symbol = evdev.ecodes.ABS[evdev_event.code]

    elif evdev_event.type == evdev.events.EV_KEY:
        if evdev_event.value == evdev.events.KeyEvent.key_up:
            kind = EVENT_KEYRELEASE
        elif evdev_event.value == evdev.events.KeyEvent.key_down:
            kind = EVENT_KEYPRESS
        elif evdev_event.value == evdev.events.KeyEvent.key_hold:
            kind = EVENT_KEYHOLD
        else:
            raise UnhandledEvent("Unhandled evdev.InputEvent.value %d" % evdev_event.value)

        symbol = evdev.events.keys[evdev_event.code]
        if isinstance(symbol, list):
            # More than one symbol for that code
            symbol = symbol[0]

    else:
        raise UnhandledEvent("Unhandled evdev.InputEvent.type %d" % evdev_event.type)

    return events.Event(kind, code, symbol, evdev_event.value)


def _open_device(path):
    device = evdev.InputDevice(path)
    logger.info("Opened device %s (%s)", device.fn, device.name)
    return device


class EvdevReader(base.BaseReader):
    """Low-level evdev reader.

    Handles:
    - Reading lines
    - Exclusive device access
    - Conversion into Event

    Attributes:
        device (evdev.InputDevice): the device to read from
        filter (Filter): helper to filter events at the source
        exclusive (bool): whether to grab exclusive hold of the device while
            reading
    """

    def __init__(self, device_path, filter=None, exclusive=True, **kwargs):
        super(EvdevReader, self).__init__(**kwargs)
        self.device = _open_device(device_path)
        self.filter = filter
        self.exclusive = exclusive

    def setup(self):
        super(EvdevReader, self).setup()
        if self.exclusive:
            logger.info("Grabbing exclusive use of %s", self.device)
            self.device.grab()

    def convert_event(self, event):
        """Try to convert an evdev.events.InputEvent into an Event."""
        try:
            return _map_event(event)
        except UnhandledEvent:
            logger.debug("Skipping unhandled event %s", event, exc_info=True)
            return None

    def read(self):
        """Read data from the evdev InputDevice.

        Yields:
            evdev.events.InputEvent
        """
        for evdev_event in self.device.read_loop():
            event = self.convert_event(evdev_event)
            if event is not None and self.filter.should_send(event):
                yield event

    def cleanup(self):
        # closing the device also ungrabs it
        self.device.close()
        super(EvdevReader, self).cleanup()


class EvdevDirReader(base.BaseReader):
    """Low-level evdev reader that captures events from devices
    residing in a directory.

    Handles:
    - Reading lines
    - Subscriptions to devices
    - Exclusive device access
    - Conversion into Event

    Attributes:
        devices (dict of str: evdev.InputDevice): devices to read from
        dir_path (str): path to the directory
        filter (Filter): helper to filter events at the sources
        exclusive (bool): whether to grab exclusive hold of devices while
            reading
    """

    class EventHandler(FileSystemEventHandler):
        def __init__(self, reader):
            self.reader = reader

        def on_created(self, event):
            self.reader.register_device(event.src_path)

        def on_deleted(self, event):
            self.reader.unregister_device(event.src_path)

    def __init__(self, dir_path, filter=None, exclusive=True, **kwargs):
        super(EvdevDirReader, self).__init__(**kwargs)
        self.devices = {}
        self.dir_path = dir_path
        self.exclusive = exclusive
        self.filter = filter
        self._observer = Observer()
        self._observer.schedule(
            EvdevDirReader.EventHandler(self), self.dir_path
        )

    def setup(self):
        super(EvdevDirReader, self).setup()
        for device in evdev.util.list_devices(self.dir_path):
            self.register_device(device)
        self._observer.start()

    def convert_event(self, event):
        """Try to convert an evdev.events.InputEvent into an Event."""
        try:
            return _map_event(event)
        except UnhandledEvent:
            logger.debug("Skipping unhandled event %s", event, exc_info=True)
            return None

    def read(self):
        """Read data from the evdev InputDevices.

        Yields:
            evdev.events.InputEvent
        """
        while True:
            # wait for events 5s max to detect changes in the devices map
            rlist, _, _ = select.select(
                list(self.devices.values()), [], [], 5
            )
            for device in rlist:
                # check the device is still valid in case select
                # exited early, e.g. when the device was deleted
                if evdev.util.is_device(device.path):
                    for evdev_evt in device.read():
                        evt = self.convert_event(evdev_evt)
                        if evt is not None and self.filter.should_send(evt):
                            yield evt

    def cleanup(self):
        self._observer.stop()
        for device_path in list(self.devices.keys()):
            self.unregister_device(device_path)
        super(EvdevDirReader, self).cleanup()

    def register_device(self, device_path):
        if evdev.util.is_device(device_path):
            logger.debug("Registering device at %s", device_path)
            device = _open_device(device_path)
            if self.exclusive:
                device.grab()
            self.devices[device_path] = device

    def unregister_device(self, device_path):
        device = self.devices.pop(device_path, None)
        if device:
            logger.debug("Unregistering device at %s", device_path)
            # closing the device also ungrabs it
            device.close()
