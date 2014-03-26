"""
aspen.logging
+++++++++++++

Aspen logging. It's simple.

There are log and log_dammit functions that take arbitrary positional
arguments, stringify them, write them to stdout, and flush stdout. Each line
written is prepended with process and thread identifiers. The philosophy is
that additional abstraction layers above Aspen can handle timestamping along
with piping to files, rotation, etc. PID and thread id are best handled inside
the process, however.

The LOGGING_THRESHOLD attribute controls the amount of information that will be
logged. The level kwarg to log must be greater than or equal to the threshold
for the message to get through. Aspen itself logs at levels zero (via log with
the default level value) and one (with the log_dammit wrapper). It's expected
that your application will have its own wrapper(s).

Unicode objects are encoded as UTF-8. Bytestrings are passed through as-is.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from __future__ import with_statement
import os
import pprint
import sys
import thread
import threading


LOGGING_THRESHOLD = -1
PID = os.getpid()
LOCK = threading.Lock()


def stringify(o):
    """Given an object, return a str, never raising ever.
    """
    if isinstance(o, str):
        o = o
    elif isinstance(o, unicode):
        o = o.encode('UTF-8', 'backslashreplace')
    else:
        o = pprint.pformat(o)
    return o


def log(*messages, **kw):
    level = kw.get('level', 0)
    if level >= LOGGING_THRESHOLD:
        # Be sure to use Python 2.5-compatible threading API.
        t = threading.currentThread()
        fmt = "pid-%s thread-%s (%s) %%s" % ( PID
                                            , thread.get_ident()
                                            , t.getName()
                                             )
        for message in messages:
            message = stringify(message)
            for line in message.splitlines():
                with LOCK:
                    # Log lines can get interleaved, but that's okay, because
                    # we prepend lines with thread identifiers that can be used
                    # to reassemble log messages per-thread.
                    print(fmt % line.decode('utf8'))
                    sys.stdout.flush()


def log_dammit(*messages):
    log(*messages, **{'level': 1})
    #log(*messages, level=1)  <-- SyntaxError in Python 2.5
