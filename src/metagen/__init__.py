import sys

DEBUGGING = True


def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if DEBUGGING:
        debug_hook(exception_type, exception, traceback)
    else:
        print(str(exception_type.__name__) + ": " +
              str(exception), file=sys.stderr)


sys.excepthook = exception_handler
