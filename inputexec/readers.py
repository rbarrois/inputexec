

"""Reads inputs."""

import evdev


class KeyEvent(evdev.events.KeyEvent):
    def __init__(self, *args, **kwargs):
        super(KeyEvent, self).__init__(*args, **kwargs)
        if isinstance(self.keycode, list):
            # More than one option, keep the first
            self.keycode = self.keycode[0]


class RawReader(object):
    def __init__(self, device, evdev_device=None, **kwargs):
        super(RawReader, self).__init__(**kwargs)
        if evdev_device is None:
            evdev_device = evdev.InputDevice(device)
        self.device = evdev_device

    def read(self, exclusive=True):
        if exclusive:
            self.device.grab()

        try:
            for event in self.device.read_loop():
                yield event
        finally:
            if exclusive:
                self.device.ungrab()


class Filter(object):
    def __init__(self, kinds=(evdev.events.EV_KEY,), actions=(evdev.events.KeyEvent.key_up,), **kwargs):
        super(Filter, self).__init__(**kwargs)
        self.kinds = kinds
        self.actions = actions

    def apply(self, event):
        return event.type in self.kinds and event.value in self.actions


class Mapper(object):
    def map(self, event):
        if event.type == evdev.events.EV_KEY:
            return KeyEvent(event)
        else:
            return evdev.categorize(event)


class Reader(object):
    def __init__(self, device, filter=None, mapper=None):
        self.raw = RawReader(device)
        self._filter = filter or Filter()
        self.mapper = mapper or Mapper()

    def should_send(self, event):
        return self._filter is None or self._filter.apply(event)

    def read(self, exclusive=True):
        for event in self.raw.read(exclusive):
            if self.should_send(event):
                yield self.mapper.map(event)



