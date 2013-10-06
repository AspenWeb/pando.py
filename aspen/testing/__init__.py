from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import aspen.logging
if aspen.logging.LOGGING_THRESHOLD == -1:
    # Suppress aspen's logging during tests.
    aspen.logging.LOGGING_THRESHOLD = 3
from aspen import resources
from aspen.http.request import Request
from aspen.website import Website
from aspen.utils import typecheck
from aspen.testing.fsfix import fix, FSFIX, mk, teardown, teardown_function


__all__ = ['fix', 'teardown', 'handle', 'teardown_function']


class Stub:
    pass

class StubBody:
    def read(self):
        return b''
    def __iter__(self):
        yield b''

def StubWSGIRequest(path=b'/'):
    environ = {}
    environ['PATH_INFO'] = path
    environ['REMOTE_ADDR'] = b'0.0.0.0'
    environ['REQUEST_METHOD'] = b'GET'
    environ['SERVER_PROTOCOL'] = b'HTTP/1.1'
    environ['HTTP_HOST'] = b'localhost'
    environ['wsgi.input'] = StubBody()
    return environ

class StubRequest:

    def __call__(cls, uripath=b'/'):
        typecheck(uripath, str)
        return Request.from_wsgi(StubWSGIRequest(uripath))

    @classmethod
    def from_fs(cls, fs, *a):
        """Takes a path under FSFIX using / as the path separator.
        """
        fs = os.sep.join(fs.split(os.sep))
        uri_path = fs
        if fs.endswith('.spt'):
            uri_path = fs[:-4]
        request = Request.from_wsgi(StubWSGIRequest(uri_path))
        website = Website([ '--www_root', FSFIX
                          , '--project_root', os.path.join(FSFIX, '.aspen')
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
        path = path.encode('ascii') # StubRequest/Request takes bytestings only.
        website = Website(self.argv + list(a))
        request = StubRequest(path)
        request.website = website
        response = website.handle_safely(request)
        return response

handle = Handle(['--www_root', FSFIX, '--show_tracebacks=yes'])


def Resource(fs):
    return resources.load(StubRequest.from_fs(fs), 0)

def check(content, filename="index.html.spt", body=True, configure_aspen_py="",
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

NoException = True
