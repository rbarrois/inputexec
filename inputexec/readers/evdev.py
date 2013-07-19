# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import absolute_import
from __future__ import unicode_literals

"""Reads inputs from an evdev device."""

import evdev
import logging

from .. import events

from . import base


logger = logging.getLogger(__name__)


class UnhandledEvent(Exception):
    pass


EVENT_SYNC = 'sync'
EVENT_KEYPRESS = 'keypress'
EVENT_KEYHOLD = 'keyhold'
EVENT_KEYRELEASE = 'keyrelease'
EVENT_RELMOVE = 'relmove'
EVENT_ABSMOVE = 'absmove'


def map_event(evdev_event):

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
            # More than on symbol for that code
            symbol = symbol[0]

    else:
        raise UnhandledEvent("Unhandled evdev.InputEvent.type %d" % evdev_event.type)

    return events.Event(kind, code, symbol, evdev_event.value)


class Filter(object):
    """Filters events."""
    def __init__(self, kinds=(EVENT_KEYPRESS,), **kwargs):
        super(Filter, self).__init__(**kwargs)
        self.kinds = kinds

    def should_send(self, event):
        """Whether an Event should be handled."""
        return event.kind in self.kinds


def open_device(path):
    device = evdev.InputDevice(path)
    logger.info("Opened device %s (%s)", device.fn, device.name)
    return device


class EvdevReader(base.BaseReader):
    """Low-level evdev reader.

    Handles:
    - Reading lines
    - exclusive device access
    - Conversion into Event.

    Attributes:
        device (evdev.InputDevice): the device to read from
        filter (Filter): helper to filter events at the source
        exclusive (bool): whether to grab exclusive hold of the device while
            reading
    """

    def __init__(self, evdev_device, filter=None, exclusive=True, **kwargs):
        super(EvdevReader, self).__init__(**kwargs)
        self.device = evdev_device
        self.filter = filter
        self.exclusive = exclusive

    def setup(self):
        super(EvdevReader, self).setup()
        if self.exclusive:
            logger.info("Grapping exclusive use of %s", self.device)
            self.device.grab()

    def convert_event(self, event):
        """Try to convert a evdev.events.InputEvent into an Event."""
        try:
            return map_event(event)
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
        if self.exclusive:
            self.device.ungrab()
        super(EvdevReader, self).cleanup()
