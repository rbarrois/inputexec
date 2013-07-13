class BaseExecutor(object):
    def handle(self, event):
        """Handle an event."""
        raise NotImplementedError()


class PrintingExecutor(BaseExecutor):
    def __init__(self, out, end_line='\n', **kwargs):
        self.out = out
        self.end_line = end_line
        super(PrintingExecutor, self).__init__(**kwargs)

    def handle(self, event):
        self.out.write(event.keycode)
        self.out.write(self.end_line)
        self.out.flush()


class RunningExecutor(BaseExecutor):

    def handle(self, event):
        pass
