class BaseExecutor(object):
    def __init__(self, config, **kwargs):
        super(BaseExecutor, self).__init__(**kwargs)
        self.config = config

    def handle(self, event):
        """Handle an event."""
        raise NotImplementedError()


class PrintingExecutor(BaseExecutor):
    def handle(self, event):
        out = self.config.out
        out.write(event.keycode)
        out.write('\n')

