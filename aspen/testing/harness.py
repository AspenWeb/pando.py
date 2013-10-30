from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
from Cookie import SimpleCookie
from StringIO import StringIO

from aspen.network_engines import ThreadedBuffer
from aspen.http.request import Request
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.sockets.transport import XHRPollingTransport
from aspen.website import Website


BOUNDARY = 'BoUnDaRyStRiNg'
MULTIPART_CONTENT = 'multipart/form-data; boundary=%s' % BOUNDARY


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
            '--' + boundary,
            'Content-Disposition: form-data; name="%s"' % str(key),
            '',
            str(value)
        ])

    lines.extend([
        '--' + boundary + '--',
        '',
    ])
    return '\r\n'.join(lines)


class Harness(object):
    """
    The Aspen testing harness.

    Used in tests to emulate ``GET`` and ``POST`` requests by sending them
    into a ``Website`` instance's ``respond`` method.

    Aspen does not define any User data structures or modules. If you want to
    do anything with users/sessions etc in your tests it is expected that you
    will subclass this class and add a ``add_cookie_info`` method.

    For example, in gittip a suitable subclass might be::

        class GittipTestClient(TestClient):

            def add_cookie_info(self, request, cookie_info):
                if cookie_info:
                    user = cookie_info.get('user')
                    if user is not None:
                        user = User.from_id(user)
                        # Note that Cookie needs a bytestring.
                        request.headers.cookie['session'] = user.session_token

    Example usage in a test::

        def test_api_handles_posts():
            client = TestClient(website)

            # We need to get ourselves a token!
            response = client.get('/')
            csrf_token = response.request.context['csrf_token']

            # Then, add a $1.50 and $3.00 tip
            response = client.post("/test_tippee1/tip.json",
                                {'amount': "1.00", 'csrf_token': csrf_token},
                                cookie_info={'user': 'test_tipper'})

            # Confirm we get back the right amounts in the JSON body.
            first_data = json.loads(response.body)
            assert_equal(first_data['amount'], "1.00")
    """

    def __init__(self, www, project):
        self.fs = namedtuple('fs', 'www project')
        self.fs.www = www
        self.fs.project = project
        self.argv = []
        self.cookies = SimpleCookie()
        self.want_short_circuit = True
        self._website = None


    # HTTP Methods
    # ============

    def _prime_website(self):
        if self._website is None:
            argv = [ '--www_root', self.fs.www.root
                   , '--project_root', self.fs.project.root
                   , '--show_tracebacks', '1'
                    ] + self.argv
            self._website = Website(argv)
            self.website.flow.want_short_circuit = self.want_short_circuit
        return self._website
    website = property(_prime_website)


    def GET(self, path='/', cookie_info=None, run_through=None, **extra):
        self._prime_website()
        environ = self._build_wsgi_environ(path, "GET", **extra)
        return self._perform_request(environ, cookie_info, run_through)


    def POST(self, path='/', data=None, content_type=MULTIPART_CONTENT, cookie_info=None,
            run_through=None, **extra):
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
        self._prime_website()
        post_data = data if data is not None else {}

        if content_type is MULTIPART_CONTENT:
            post_data = encode_multipart(BOUNDARY, data)

        environ = self._build_wsgi_environ( path
                                          , "POST"
                                          , post_data
                                          , CONTENT_TYPE=str(content_type)
                                          , **extra
                                           )
        return self._perform_request(environ, cookie_info, run_through)


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

    def make_request(self, filename='echo.sock.spt'):
        request = Request(uri='/echo.sock')
        request.website = self.website
        request.fs = self.fs.www.resolve(filename)
        return request

    def make_socket(self, filename='echo.sock.spt', channel=None):
        request = self.make_request(filename='echo.sock.spt')
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


    # Hook
    # ====

    def add_cookie_info(self, request, **cookie_info):
        """Place holder function that can be replaced in a subclass.

        For example in gittip.com, it might be of interest to load session
        information into the cookie like this::

            if cookie_info:
                user = cookie_info.get('user')
                if user is not None:
                    user = User.from_id(user)
                    # Note that Cookie needs a bytestring.
                    request.headers.cookie['session'] = user.session_token
        """
        pass


    # Helpers
    # =======

    def _build_wsgi_environ(self, path, method="GET", body=None, **extra):
        environ = {}
        environ['PATH_INFO'] = path
        environ['REMOTE_ADDR'] = b'0.0.0.0'
        environ['REQUEST_METHOD'] = b'GET'
        environ['SERVER_PROTOCOL'] = b'HTTP/1.1'
        environ['HTTP_HOST'] = b'localhost'
        environ['REQUEST_METHOD'] = method
        environ['wsgi.input'] = StringIO(body)
        environ['HTTP_COOKIE'] = self.cookies.output(header='', sep='; ')
        environ.update(extra)
        return environ


    def _perform_request(self, environ, cookie_info, run_through):
        self.add_cookie_info(environ, **(cookie_info or {}))
        out = self.website.respond(environ, _run_through=run_through)
        if run_through is None:
            response = out
        else:
            response = out['response']
        if response is not None:
            if response.headers.cookie:
                self.cookies.update(response.headers.cookie)
        return out
