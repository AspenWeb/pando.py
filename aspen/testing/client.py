from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from Cookie import SimpleCookie
from StringIO import StringIO

from aspen.server import Server
from aspen.utils import typecheck


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


class Client(object):
    """This is the Aspen test client.

    Used in tests to emulate ``GET`` and ``POST`` requests by sending them into
    a ``Website`` instance's ``respond`` method.

    """

    def __init__(self, www_root=None, project_root=None):
        self.www_root = www_root
        self.project_root = project_root
        self.cookie = SimpleCookie()
        self._website = None

    def hydrate_website(self, argv=None):
        if (self._website is None) or (argv is not None):
            argv = [ '--www_root', self.www_root
                   , '--project_root', self.project_root
                    ] + ([] if argv is None else argv)
            self._website = Server(argv).get_website()
        return self._website
    website = property(hydrate_website)


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
