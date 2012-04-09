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


from aspen import Response
from aspen.configuration import Configurable
from aspen.http.request import Request
from aspen.resources import load
from aspen.website import Website
from aspen._tornado.template import Loader
from aspen.testing.fsfix import fix, attach_teardown, FSFIX, mk, teardown


__all__ = ['assert_raises', 'attach_teardown', 'fix', 'teardown']


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
        """Takes a path under FSFIX using / as the path separator.
        """
        fs = os.sep.join(fs.split(os.sep))
        request = Request.from_wsgi(StubWSGIRequest(fs))
        website = Configurable.from_argv(['--root', FSFIX])
        website.copy_configuration_to(request)
        #request.root = join(dirname(__file__), FSFIX)
        request.fs = fs
        request.context = {}
        request.website = website 
        request.website.template_loader = Stub()
        return request

StubRequest = StubRequest()


class Handle(object):
    """Stub out website.handle with set configuration.
    """

    def __init__(self, argv):
        """Takes an argv list.
        """
        self.argv = argv

    def __call__(self, path='/'):
        """Given an URL path, return 

        This only allows you to simulate GET requests with no querystring, so
        it's limited. But it's a something. Kind of. Almost.

        """
        website = Website(self.argv)
        request = StubRequest(path)
        request.website = website
        response = website.handle(request)
        return response

handle = Handle(['--root', FSFIX])


def Resource(fs):
    return load(StubRequest.from_fs(fs), 0)

def check(content, filename="index.html", body=True, aspenconf="", 
        response=None):
    mk(('.aspen/aspen.conf', aspenconf), (filename, content))
    request = StubRequest.from_fs(filename)
    response = response or Response()
    resource = load(request, 0)
    response = resource.respond(request, response)
    if body:
        return response.body
    else:
        return response

def assert_raises(Exc, call, *arg, **kw):
    """Given an Exception, a callable, and its params, return an exception.

    If the callable does not raise an exception then AssertionError will be
    raised with a message indicating as much. Likewise if the callable raises a
    different exception than what was expected.

    """
    exc = None
    try:
        call(*arg, **kw)
    except:
        exc = sys.exc_info()[1]
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (repr(exc), repr(Exc))
    return exc

NoException = True
