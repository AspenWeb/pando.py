import errno
import logging
import os
import sys
import time
import urllib
from os.path import join

from aspen.configuration import Configuration
from aspen.http.request import Request
from aspen.website import Website
from diesel.protocols.http import HttpHeaders, HttpRequest
from aspen._tornado.template import Loader


def DieselReq(path='/'):
    diesel_request = HttpRequest('GET', path, 'HTTP/1.1')
    diesel_request.headers = HttpHeaders(Host='localhost') # else 400 in hydrate
    return diesel_request

def handle(path):
    website = Website(Configuration(['fsfix']))
    request = Request.from_diesel(DieselReq(path))
    request.website = website
    return website.handle(request)



# Logging
# =======
# We keep one root log handler around during testing, it logs unbuffered to 
# stdout. By default for all tests it only outputs messages filtered with 
# 'aspen.tests'; you can use the `log' logger for that.
#
# If your test needs to check log output from another subsystem, call the 
# filter() method during setup. All logging is reset on teardown.

TEST_SUBSYSTEM = 'aspen.tests'
LOG = os.path.realpath('log')

def set_log_filter(filter):
    """Change the logging subsystem filter.
    """
    root = logging.getLogger()
    handler = root.handlers[0]
    filter = logging.Filter(filter)
    handler.filters = [filter]

def reset_log_filter():
    root = logging.getLogger()
    handler = root.handlers[0]
    for filter in handler.filters:
        handler.removeFilter(filter)
    set_log_filter(TEST_SUBSYSTEM)


def set_log_format(format):
    """Change the logging format.
    """
    root = logging.getLogger()
    handler = root.handlers[0]
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)

def reset_log_format():
    set_log_format("%(message)s")


log = logging.getLogger(TEST_SUBSYSTEM)


class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        logging.StreamHandler.emit(self, record)
        self.flush()

def configure_logging():
    """Using the logging subsystem, send messages from 'aspen.tests' to ./log.
    """
#    logging.raiseExceptions = False
#    logging.shutdown() # @@: triggers
#    logging.raiseExceptions = True 

    fp = open(LOG, 'a') # log is truncated in teardown func in fsfix.py
    handler = FlushingStreamHandler(fp)
    handler.setLevel(0)     # everything

    root = logging.getLogger()
    root.setLevel(0) # everything, still
    root.handlers = [handler]

    set_log_filter(TEST_SUBSYSTEM)

configure_logging()


# Asserters
# =========
# The first two are useful if you want a test generator.

def assert_(expr):
    assert expr

def assert_actual(expected, actual):
    assert actual == expected, actual

def assert_logs(*lines, **kw):
    if lines[0] is None:
        expected = ''
    else:
        # when logged output is printed, system-specific newlines are used
        # when logged output is written to a file, universal newline support 
        #  kicks in, and we have to work around it here
        force_unix_EOL = kw.get('force_unix_EOL', False)
        linesep = force_unix_EOL and '\n' or os.linesep
        expected = linesep.join(lines) + linesep
    actual = kw.get('actual', open(LOG, 'r').read())
    assert actual == expected, actual.splitlines()

def assert_prints(*args):
    args = list(args)
    expected = args[:-1]
    actual = args[-1]
    assert_logs(*expected, **{'actual':actual}) # a little goofy, yes

def assert_raises(Exc, call, *arg, **kw):
    """Given an Exception, a callable, and its params, return an exception.
    """
    exc = None
    try:
        call(*arg, **kw)
    except (SystemExit, Exception), exc: # SystemExit isn't an Exception?!
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (repr(exc), repr(Exc))
    return exc
