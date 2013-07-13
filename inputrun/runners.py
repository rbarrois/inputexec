

class Runner(object):
    def __init__(self, reader, formatter, output, end_line='\n', **kwargs):
        super(Runner, self).__init__(**kwargs)
        self.reader = reader
        self.formatter = formatter
        self.output = output
        self.end_line = end_line

    def run(self, exclusive=True, close_output=False):
        try:
            for event in self.reader.read(exclusive):
                self.output.write(self.formatter.format(event))
                self.output.write(self.end_line)
                self.output.flush()
        finally:
            if close_output:
                self.output.close()
