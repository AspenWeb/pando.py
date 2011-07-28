import errno
import inspect
import os
import sys
import time
import traceback
import urllib
from os.path import dirname, join

import threading
import collections
def _log(*a):
    things = collections.deque(a)
    things.appendleft(threading.current_thread().name.ljust(12))
    while things:
        thing = things.popleft()
        sys.stdout.write(str(thing))
        if things:
            sys.stdout.write(" ")
    print


from aspen.configuration import Configurable
from aspen.http.request import Request
from aspen.website import Website
from aspen._tornado.template import Loader


def print_stack():
    """Print the current stack trace.
    """
    previous_frame = inspect.stack()[1][0] # strip off ourselves
    for line in traceback.format_stack(previous_frame):
        sys.stdout.write(line)


class Stub:
    pass

class StubBody:
    def read(self):
        return ''

def StubWSGIRequest(path='/'):
    environ = {}
    environ['PATH_INFO'] = path
    environ['REMOTE_ADDR'] = '0.0.0.0'
    environ['REQUEST_METHOD'] = 'GET'
    environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
    environ['HTTP_HOST'] = 'localhost'
    environ['wsgi.input'] = StubBody()
    return environ

class StubRequest:
    
    def __call__(cls, path='/'):
        return Request.from_wsgi(StubWSGIRequest(path))

    @classmethod
    def from_fs(cls, fs):
        """Takes a path under ./fsfix using / as the path separator.
        """
        fs = os.sep.join(fs.split('/'))
        request = Request.from_wsgi(StubWSGIRequest(fs))
        website = Configurable.from_argv(['fsfix'])
        website.copy_configuration_to(request)
        request.root = join(dirname(__file__), 'fsfix')
        request.fs = fs
        request.namespace = {}
        request.website = website 
        request.website.template_loader = Stub()
        return request

StubRequest = StubRequest()


def handle(path='/'):
    website = Website(['fsfix'])
    request = StubRequest(path)
    request.website = website
    response = website.handle(request)
    return response


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
