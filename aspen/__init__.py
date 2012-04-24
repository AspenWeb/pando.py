import os
import sys
import thread
import threading

try:                # Python >= 2.6
    from collections import Callable
    def is_callable(obj):
        return isinstance(obj, Callable)
except ImportError: # Python < 2.6
    from operator import isCallable as is_callable

# imports of convenience
from aspen.http.response import Response
from aspen import json_ as json
Response, json, is_callable  # Shut up, PyFlakes. I know I'm addicted to you.


__version__ = "~~VERSION~~"
WINDOWS = sys.platform[:3] == 'win'
ENGINES = ['cheroot', 'cherrypy', 'diesel', 'eventlet', 'gevent', 'pants', 
           'rocket', 'tornado', 'twisted']


# Logging. It's simple.
# =====================

# set to 1 and only really important things (startup/shutdown and tracebacks)
# will be logged. If you pass -q2 nothing will be logged by aspen.

LOGGING_THRESHOLD = 0

_pid = os.getpid()
def log(message, level=0):
    message = unicode(message).encode('UTF-8', 'backslashreplace') # XXX buggy?
    if level >= LOGGING_THRESHOLD:
        # Be sure to use Python 2.5-compatible threading API.
        t = threading.currentThread()
        for line in message.splitlines():
            print "pid-%s thread-%s (%s) %s" % ( _pid
                                               , thread.get_ident()
                                               , t.getName()
                                               , line
                                                )
        sys.stdout.flush()

def log_dammit(message):
    log(message, level=1)
