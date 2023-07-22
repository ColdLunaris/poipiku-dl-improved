"""
I shamelessly stole this from here because it looks cool when writing to stdout
https://stackoverflow.com/questions/63667943/python-print-status-lines-orphaned-characters-from-previous-print-at-the-end
"""

import sys

class print_status():
    __status_colors = {
        'ok' : '\33[32;1m',
        'failed' : '\33[31;1m',
        'wait' : '\33[33;1m',
        'blue' : '\33[34;1m'
    }

    def __init__(self, text, status, single=False):
        self.text = text
        self.stat = status
        if single:
            self.output(self.text, self.stat, carriageret=False, newline=True)
        else:
            self.output(self.text, self.stat, carriageret=True, newline=False)

    def _get_color(self, stat):
        try:
            c = self.__status_colors[stat]
        except KeyError:
            c = '\033[0;1m'
        return c
    
    def output(self, text=False, status=False, carriageret=False, newline=False):
        if not text:
            text = self.text
        if not status:
            status = self.stat

        col = self._get_color(status)
        cr = '\r\x1b[2K' if carriageret == True else ''
        nl = '\n' if newline == True else ''

        s = (cr + '[' + col + status + '\033[0m' + '] ' + text + nl)
        sys.stdout.write(s)
        sys.stdout.flush()

    def last(self, text=False, status=False):
        self.output(text, status, carriageret=True, newline=True)
        del self.text
        del self.stat

    def update(self, text=False, status=False):
        self.output(text, status, carriageret=True, newline=False)

