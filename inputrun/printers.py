

class BaseFormatter(object):
    def format(self, event):
        raise NotImplementedError()


class SimpleFormatter(BaseFormatter):
    def __init__(self, kind=False, code=False, symbol=True, separator=' ', **kwargs):
        super(SimpleFormatter, self).__init__(**kwargs)

        self.kind = kind
        self.code = code
        self.symbol = symbol

    def format(self, event):
        parts = []
        if self.kind:
            parts.append(event.keystate)
        if self.code:
            parts.append(event.scancode)
        if self.symbol:
            parts.append(event.keycode)

        return self.separator.join(parts)


class PatternFormatter(BaseFormatter):
    def __init__(self, pattern, **kwargs):
        super(PatternFormatter, self).__init__(**kwargs)
        self.pattern = pattern

    def format(self, event):
        fields = {
            'kind': event.keystate,
            'code': event.scancode,
            'symbol': event.keycode,
        }

        return self.pattern.format(**fields)
