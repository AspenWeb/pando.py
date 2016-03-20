"""
pando.testing.client
~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from Cookie import SimpleCookie
from StringIO import StringIO

import mimetypes
from .. import Response
from ..utils import typecheck
from ..website import Website

BOUNDARY = b'BoUnDaRyStRiNg'
MULTIPART_CONTENT = b'multipart/form-data; boundary=%s' % BOUNDARY


class DidntRaiseResponse(Exception): pass


class FileUpload(object):
    """Model a file upload for testing. Takes data and a filename.
    """

    def __init__(self, data, filename, content_type=None):
        self.data = data
        self.filename = filename
        self.content_type = content_type or mimetypes.guess_type(filename)[0]


def encode_multipart(boundary, data):
    """
    Encodes multipart POST data from a dictionary of form values.

    The key will be used as the form data name; the value will be transmitted
    as content. Use the FileUpload class to simulate file uploads (note that
    they still come out as FieldStorage instances inside of simplates).

    """
    lines = []

    for (key, value) in data.items():
        if isinstance(value, FileUpload):
            file_upload = value
            lines.extend([
                b'--' + boundary,
                b'Content-Disposition: form-data; name="{}"; filename="{}"'
                 .format(str(key), str(file_upload.filename)),
                b'Content-Type: {}'.format(file_upload.content_type),
                b'',
                str(file_upload.data)
            ])
        else:
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
    """This is the Pando test client. It is probably useful to you.
    """

    def __init__(self, www_root=None, project_root=None):
        self.www_root = www_root
        self.project_root = project_root
        self.cookie = SimpleCookie()
        self._website = None


    def hydrate_website(self, **kwargs):
        if (self._website is None) or kwargs:
            _kwargs = { 'www_root': self.www_root
                      , 'project_root': self.project_root
                       }
            _kwargs.update(kwargs)
            self._website = Website(**_kwargs)
        return self._website

    website = property(hydrate_website)


    def load_resource(self, path):
        """Given an URL path, return a Resource instance.
        """
        return self.hit('GET', path=path, return_after='get_resource_for_request', want='resource')


    # HTTP Methods
    # ============

    def GET(self, *a, **kw):    return self.hit('GET', *a, **kw)
    def POST(self, *a, **kw):   return self.hit('POST', *a, **kw)

    def GxT(self, *a, **kw):    return self.hxt('GET', *a, **kw)
    def PxST(self, *a, **kw):   return self.hxt('POST', *a, **kw)

    def hxt(self, *a, **kw):
        try:
            self.hit(*a, **kw)
        except Response as response:
            return response
        else:
            raise DidntRaiseResponse

    def hit(self, method, path='/', data=None, body=b'', content_type=MULTIPART_CONTENT,
            raise_immediately=True, return_after=None, want='response', **headers):

        data = {} if data is None else data
        if content_type is MULTIPART_CONTENT:
            body = encode_multipart(BOUNDARY, data)

        environ = self.build_wsgi_environ(method, path, body, str(content_type), **headers)
        state = self.website.respond( environ
                                    , raise_immediately=raise_immediately
                                    , return_after=return_after
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


    def build_wsgi_environ(self, method, path, body, content_type, **kw):

        # NOTE that in Pando (request.py make_franken_headers) only headers
        # beginning with ``HTTP`` are included in the request - and those are
        # changed to no longer include ``HTTP``. There are currently 2
        # exceptions to this: ``'CONTENT_TYPE'``, ``'CONTENT_LENGTH'`` which
        # are explicitly checked for.

        typecheck(path, (str, unicode), method, unicode, content_type, str, body, str)
        environ = {}
        environ[b'CONTENT_TYPE'] = content_type
        environ[b'HTTP_COOKIE'] = self.cookie.output(header=b'', sep=b'; ')
        environ[b'HTTP_HOST'] = b'localhost'
        environ[b'PATH_INFO'] = path if type(path) is str else path.decode('UTF-8')
        environ[b'REMOTE_ADDR'] = b'0.0.0.0'
        environ[b'REQUEST_METHOD'] = method.decode('ASCII')
        environ[b'SERVER_PROTOCOL'] = b'HTTP/1.1'
        environ[b'wsgi.input'] = StringIO(body)
        environ[b'HTTP_CONTENT_LENGTH'] = bytes(len(body))
        environ.update(kw)
        return environ
