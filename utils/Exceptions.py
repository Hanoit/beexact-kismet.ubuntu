import sys
import traceback


class Exceptions(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def getTraceBack():
    err = ""
    tb = sys.exc_info()[2]
    if tb:
        tb_info = traceback.format_tb(tb)[0]
        try:
            err = u'%s%s' % (tb_info, sys.exc_info())
        except:
            try:
                err = tb_info
            except:
                err = "Error inesperado."
    return err
