from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
from collections import namedtuple
from Cookie import SimpleCookie
from StringIO import StringIO

from aspen import resources, sockets
from aspen.http.request import Request
from aspen.network_engines import ThreadedBuffer
from aspen.server import Server
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.sockets.transport import XHRPollingTransport
from aspen.utils import typecheck
from filesystem_tree import FilesystemTree


CWD = os.getcwd()


def teardown():
    """Standard teardown function.

    - reset the current working directory
    - remove FSFIX = %{tempdir}/fsfix
    - reset Aspen's global state
    - clear out sys.path_importer_cache
    - clear out execution.extras

    """
    os.chdir(CWD)
    # Reset some process-global caches. Hrm ...
    resources.__cache__ = {}
    sockets.__sockets__ = {}
    sockets.__channels__ = {}
    sys.path_importer_cache = {} # see test_weird.py
    import aspen.execution
    aspen.execution.clear_changes()

teardown() # start clean


BOUNDARY = b'BoUnDaRyStRiNg'
MULTIPART_CONTENT = b'multipart/form-data; boundary=%s' % BOUNDARY


def encode_multipart(boundary, data):
    """
    Encodes multipart POST data from a dictionary of form values.

    Borrowed from Django
    The key will be used as the form data name; the value will be transmitted
    as content. If the value is a file, the contents of the file will be sent
    as an application/octet-stream; otherwise, str(value) will be sent.
    """
    lines = []

    for (key, value) in data.items():
        lines.extend([
            b'--' + boundary,
            b'Content-Disposition: form-data; name="%s"' % str(key),
            b'',
            str(value)
        ])

    lines.extend([
        b'--' + boundary + b'--',
        b'',
    ])
    return b'\r\n'.join(lines)


class AspenHarness(object):
    """This is the Aspen testing harness.

    Used in tests to emulate ``GET`` and ``POST`` requests by sending them into
    a ``Website`` instance's ``respond`` method.

    """

    def __init__(self, www_root=None, project_root=None, argv=None):
        self.fs = namedtuple('fs', 'www project')
        self.fs.www = FilesystemTree(root=www_root)
        self.fs.project = FilesystemTree(root=project_root)
        self.cookie = SimpleCookie()
        self.remake_website(argv)

    def remake_website(self, argv=None):
        argv = [ '--www_root', self.fs.www.root
               , '--project_root', self.fs.project.root
                ] + [] if argv is None else argv
        self.website = Server(argv).get_website()
        return self.website


    # HTTP Methods
    # ============

    def GET(self, *a, **kw):
        return self.perform_request('GET', *a, **kw)


    def POST(self, *a, **kw):
        """Perform a dummy POST request against the test website.

        :param path:
            The url to perform the virutal-POST to.

        :param data:
            A dictionary or list of tuples to be encoded before being POSTed.

        Any additional parameters will be sent as headers. NOTE that in Aspen
        (request.py make_franken_headers) only headers beginning with ``HTTP``
        are included in the request - and those are changed to no longer
        include ``HTTP``. There are currently 2 exceptions to this:
        ``'CONTENT_TYPE'``, ``'CONTENT_LENGTH'`` which are explicitly checked
        for.
        """
        return self.perform_request('POST', *a, **kw)


    def perform_request(self, method, path='/', data=None, content_type=MULTIPART_CONTENT,
            raise_immediately=True, stop_after=None, want='response', **headers):

        data = {} if data is None else data
        if content_type is MULTIPART_CONTENT:
            body = encode_multipart(BOUNDARY, data)
        headers['CONTENT_TYPE'] = str(content_type)

        environ = self.build_wsgi_environ(method, path, body, **headers)
        state = self.website.respond( environ
                                    , raise_immediately=raise_immediately
                                    , stop_after=stop_after
                                     )

        response = state.get('response')
        if response is not None:
            if response.headers.cookie:
                self.cookie.update(response.headers.cookie)

        attr_path = want.split('.')
        base = attr_path[0]
        attr_path = attr_path[1:]

        out = state[base]
        for name in attr_path:
            out = getattr(out, name)

        return out


    def build_wsgi_environ(self, method, path, body, **kw):
        typecheck(path, (str, unicode), method, unicode)
        environ = {}
        environ[b'PATH_INFO'] = path if type(path) is str else path.decode('UTF-8')
        environ[b'REMOTE_ADDR'] = b'0.0.0.0'
        environ[b'REQUEST_METHOD'] = b'GET'
        environ[b'SERVER_PROTOCOL'] = b'HTTP/1.1'
        environ[b'HTTP_HOST'] = b'localhost'
        environ[b'REQUEST_METHOD'] = method.decode('ASCII')
        environ[b'wsgi.input'] = StringIO(body)
        environ[b'HTTP_COOKIE'] = self.cookie.output(header=b'', sep=b'; ')
        environ.update(kw)
        return environ


class _AspenHarness(AspenHarness):
    """A subclass of the test harness to be used in the Aspen test suite.
    """

    def teardown(self):
        self.fs.www.remove()
        self.fs.project.remove()


    # Simple API
    # ==========

    def simple(self, contents='Greetings, program!', filepath='index.html.spt', uripath=None,
            argv=None, **kw):
        """A helper to create a file and hit it through our machinery.
        """
        if filepath is not None:
            self.fs.www.mk((filepath, contents))
        if argv is not None:
            self.remake_website(argv)

        if uripath is None:
            if filepath is None:
                uripath = '/'
            else:
                uripath = '/' + filepath
                if uripath.endswith('.spt'):
                    uripath = uripath[:-len('.spt')]
                for indexname in self.website.indices:
                    if uripath.endswith(indexname):
                        uripath = uripath[:-len(indexname)]
                        break

        return self.GET(uripath, **kw)

    def make_request(self, *a, **kw):
        kw['stop_after'] = 'dispatch_request_to_filesystem'
        kw['want'] = 'request'
        return self.simple(*a, **kw)


    # Sockets
    # =======

    def make_transport(self, content='', state=0):
        self.fs.www.mk(('echo.sock.spt', content))
        socket = self.make_socket()
        transport = XHRPollingTransport(socket)
        transport.timeout = 0.05 # for testing, could screw up the test
        if state == 1:
            transport.respond(Request(uri='/echo.sock'))
        return transport

    def make_socket_request(self, filename='echo.sock.spt'):
        request = Request(uri='/echo.sock')
        request.website = self.website
        request.fs = self.fs.www.resolve(filename)
        return request

    def make_socket(self, filename='echo.sock.spt', channel=None):
        request = self.make_socket_request(filename='echo.sock.spt')
        if channel is None:
            channel = Channel(request.line.uri.path.raw, ThreadedBuffer)
        socket = Socket(request, channel)
        return socket

    def SocketInThread(harness):

        class _SocketInThread(object):

            def __enter__(self, filename='echo.sock.spt'):
                self.socket = harness.make_socket(filename)
                self.socket.loop.start()
                return self.socket

            def __exit__(self, *a):
                self.socket.loop.stop()

        return _SocketInThread()
