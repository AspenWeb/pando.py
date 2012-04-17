import os
import sys
import threading
import time

try:                # Python >= 2.6
    from collections import Callable
    def is_callable(obj):
        return isinstance(obj, Callable)
except ImportError: # Python < 2.6
    from operator import isCallable as is_callable

# imports of convenience
from aspen.http.response import Response
from aspen import json_ as json
Response, json # Shut up, PyFlakes. I know I'm dependent on you.


__version__ = "~~VERSION~~"
WINDOWS = sys.platform[:3] == 'win'
ENGINES = ['cheroot', 'cherrypy', 'diesel', 'eventlet', 'gevent', 'pants', 
           'rocket', 'tornado', 'twisted']


def thrash():
    """This is a very simple tool to restart a process when it dies.

    It's designed to restart aspen in development when it dies because files
    have changed and you set changes_kill to 'yes' in the [aspen.cli] section
    of aspen.conf.

    http://aspen.io/thrash/

    """
    try:
        while 1:
            os.system(' '.join(sys.argv[1:]))
            time.sleep(1)
    except KeyboardInterrupt:
        pass


# Logging. It's simple.
# =====================
# The level attribute is set in configuration/__init__.py. If you pass -q level
# will be set to 1 and only really important things (tracebacks) will be
# logged. If you pass -qq it will be set to 2 and nothing will be logged.

LOG_LEVEL = 0

_pid = os.getpid()
def log(message, level=0):
    message = unicode(message).encode('UTF-8', 'backslashreplace') # XXX buggy?
    if level >= LOG_LEVEL:
        t = threading.current_thread()
        for line in message.splitlines():  # doesn't include linebreaks 
            print "pid-%d thread-%d (%s) %s" % (_pid, t.ident, t.name, line)
        sys.stdout.flush()

def log_dammit(message):
    log(message, 1)
