import os
import sys

import aspen.logging
if aspen.logging.LOGGING_THRESHOLD == -1:
    # Suppress aspen's logging during tests.
    aspen.logging.LOGGING_THRESHOLD = 3
from aspen import resources, Response
from aspen.http.request import Request
from aspen.website import Website
from aspen.testing.fsfix import fix, attach_teardown, FSFIX, mk, teardown


__all__ = ['assert_raises', 'attach_teardown', 'fix', 'teardown']


class Stub:
    pass

class StubBody:
    def read(self):
        return ''
    def __iter__(self):
        yield ''

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

    def __call__(cls, uripath='/'):
        return Request.from_wsgi(StubWSGIRequest(uripath))

    @classmethod
    def from_fs(cls, fs, *a):
        """Takes a path under FSFIX using / as the path separator.
        """
        fs = os.sep.join(fs.split(os.sep))
        request = Request.from_wsgi(StubWSGIRequest(fs))
        website = Website([ '--www_root', FSFIX
                          , '--project_root', '.aspen'
                           ] + list(a))
        request.www_root = os.path.join(os.path.dirname(__file__), FSFIX)
        request.fs = fs
        request.context = {}
        request.website = website
        request._media_type = None
        return request

StubRequest = StubRequest()


class Handle(object):
    """Stub out website.handle_safely with set configuration.
    """

    def __init__(self, argv):
        """Takes an argv list.
        """
        self.argv = argv

    def __call__(self, path='/', *a):
        """Given an URL path, return

        This only allows you to simulate GET requests with no querystring, so
        it's limited. But it's a something. Kind of. Almost.

        """
        website = Website(self.argv + list(a))
        request = StubRequest(path)
        request.website = website
        response = website.handle_safely(request)
        return response

handle = Handle(['--www_root', FSFIX])


def Resource(fs):
    return resources.load(StubRequest.from_fs(fs), 0)

def check(content, filename="index.html", body=True, configure_aspen_py="",
        response=None, argv=None):
    if argv is None:
        argv = []
    mk(('.aspen/configure-aspen.py', configure_aspen_py), (filename, content))
    request = StubRequest.from_fs(filename, *argv)
    resource = resources.load(request, 0)
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


# Website subclass for testing simplates.
# =======================================

class TestWebsite(Website):

    def serve_request(self, path):
        """Given an URL path, return response.
        """
        request = Request(uri=path)
        request.website = self
        response = self.handle_safely(request)
        return response


    def load_simplate(self, path, request=None, return_request_too=False):
        """Given an URL path, return a simplate (Resource) object.
        """
        if request is None:
            request = Request(uri=path)
        if not hasattr(request, 'website'):
            request.website = self
        self.run_inbound(request)
        resource = resources.get(request)
        if return_request_too:
            return resource, request
        else:
            return resource


    def exec_simplate(self, path="/", request=None, response=None):
        """Given the URL path of a simplate, exec page two and return response.
        """
        resource, request = self.load_simplate(path, request, True)
        if response is None:
            response = Response(charset=self.charset_dynamic)
        context = resource.populate_context(request, response)
        exec resource.pages[1] in context  # let's let exceptions raise
        return response, context
