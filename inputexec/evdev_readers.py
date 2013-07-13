# -*- coding: utf-8 -*-
# Copyright (c) 2013 Raphaël Barrois
# This code is distributed under the 2-clause BSD License.

from __future__ import unicode_literals

"""Reads inputs from an evdev device."""

import evdev
import logging

from . import errors


logger = logging.getLogger(__name__)


class UnhandledEvent(errors.InputExecError):
    pass


class Event(object):
    """A task."""
    EVENT_SYNC = 'sync'
    EVENT_KEYPRESS = 'keypress'
    EVENT_KEYHOLD = 'keyhold'
    EVENT_KEYRELEASE = 'keyrelease'
    EVENT_RELMOVE = 'relmove'
    EVENT_ABSMOVE = 'absmove'

    def __init__(self, evdev_event):
        self.evdev_event = evdev_event
        self.code = evdev_event.code

        if evdev_event.type == evdev.events.EV_SYN:
            self.kind = self.EVENT_SYNC
            self.symbol = evdev.ecodes.SYN[evdev_event.code]

        elif evdev_event.type == evdev.events.EV_REL:
            self.kind = self.EVENT_RELMOVE
            self.symbol = evdev.ecodes.REL[evdev_event.code]

        elif evdev_event.type == evdev.events.EV_ABS:
            self.kind = self.EVENT_ABSMOVE
            self.symbol = evdev.ecodes.ABS[evdev_event.code]

        elif evdev_event.type == evdev.events.EV_KEY:
            if evdev_event.value == evdev.events.KeyEvent.key_up:
                self.kind = self.EVENT_KEYRELEASE
            elif evdev_event.value == evdev.events.KeyEvent.key_down:
                self.kind = self.EVENT_KEYPRESS
            elif evdev_event.value == evdev.events.KeyEvent.key_hold:
                self.kind = self.EVENT_KEYHOLD
            else:
                raise UnhandledEvent("Unhandled evdev.InputEvent.value %d" % evdev_event.value)

            self.symbol = evdev.events.keys[evdev_event.code]
            if isinstance(self.symbol, list):
                # More than on symbol for that code
                self.symbol = self.symbol[0]

        else:
            raise UnhandledEvent("Unhandled evdev.InputEvent.type %d" % evdev_event.type)

    def __repr__(self):
        return "<Event %s: %s>" % (self.kind, self.symbol)


class Filter(object):
    """Filters events."""
    def __init__(self, kinds=(Event.keyrelease,), **kwargs):
        super(Filter, self).__init__(**kwargs)
        self.kinds = kinds

    def should_send(self, event):
        """Whether an Event should be handled."""
        return event.kind in self.kinds


class Reader(object):
    """Low-level evdev reader.

    Handles:
    - Reading lines
    - exclusive device access
    - Conversion into Event.

    Attributes:
        device: evdev.InputDevice, the device to read from
        exclusive: bool, whether to grab exclusive hold of the device while
            reading
    """

    def __init__(self, evdev_device, filter=None, exclusive=True, **kwargs):
        super(RawReader, self).__init__(**kwargs)
        self.device = evdev_device
        self.filter = filter
        self.exclusive = exclusive

    def convert_event(self, event):
        """Try to convert a evdev.events.InputEvent into an Event."""
        try:
            return Event(event)
        except UnhandledEvent:
            logger.debug("Skipping unhandled event %s", event, exc_info=True)
            return None

    def read(self):
        """Read data from the evdev InputDevice.

        Yields:
            evdev.events.InputEvent
        """
        if self.exclusive:
            self.device.grab()

        try:
            for evdev_event in self.device.read_loop():
                event = self.convert_event(evdev_event)
                if event is not None and self.filter.should_send(event):
                    yield event

        finally:
            if self.exclusive:
                self.device.ungrab()
