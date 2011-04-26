import errno
import os
import sys
import time
import urllib
from os.path import join

import diesel.runtime
from aspen.http.request import Request
from aspen.website import Website
from diesel.protocols.http import HttpHeaders, HttpRequest
from aspen._tornado.template import Loader


def DieselReq(path='/'):
    diesel_request = HttpRequest('GET', path, 'HTTP/1.1')
    diesel_request.headers = HttpHeaders(Host='localhost') # else 400 in hydrate
    return diesel_request

def handle(path='/'):
    website = Website(['fsfix'])
    request = Request.from_diesel(DieselReq(path))
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
