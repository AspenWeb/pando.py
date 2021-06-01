"""
:mod:`client`
-------------
"""

from http.cookies import SimpleCookie
from io import BytesIO
import warnings

import mimetypes

from .. import Response
from ..utils import maybe_encode, typecheck
from ..website import Website


BOUNDARY = b'BoUnDaRyStRiNg'
MULTIPART_CONTENT = b'multipart/form-data; boundary=' + BOUNDARY


class DidntRaiseResponse(Exception):
    pass


class FileUpload:
    """Model a file upload for testing. Takes data and a filename.
    """

    def __init__(self, data, filename, content_type=None):
        self.data = data
        self.filename = filename
        self.content_type = (
            content_type or
            mimetypes.guess_type(
                filename.decode('ascii', 'backslashreplace')
            )[0].encode('ascii')
        )


def encode_multipart(boundary, data):
    """
    Encodes multipart POST data from a dictionary of form values.

    The key will be used as the form data name; the value will be transmitted
    as content. Use the FileUpload class to simulate file uploads (note that
    they still come out as FieldStorage instances inside of simplates).

    """
    lines = []

    if isinstance(data, dict):
        data = data.items()
    for key, value in data:
        if isinstance(value, FileUpload):
            file_upload = value
            lines.extend([
                b'--' + boundary,
                b'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                    key, file_upload.filename
                ),
                b'Content-Type: ' + file_upload.content_type,
                b'',
                file_upload.data
            ])
        else:
            lines.extend([
                b'--' + boundary,
                b'Content-Disposition: form-data; name="%s"' % (
                    maybe_encode(key, 'utf8')
                ),
                b'',
                maybe_encode(value, 'utf8')
            ])

    lines.extend([
        b'--' + boundary + b'--',
        b'',
    ])
    return b'\r\n'.join(lines)


class Client:
    """This is the Pando test client. It is probably useful to you.
    """

    def __init__(self, www_root=None, project_root=None):
        self.www_root = www_root
        self.project_root = project_root
        self._website = None

    def hydrate_website(self, **kwargs):
        if (self._website is None) or kwargs:
            _kwargs = {
                'www_root': self.www_root,
                'project_root': self.project_root,
            }
            _kwargs.update(kwargs)
            self._website = Website(**_kwargs)
        return self._website

    website = property(hydrate_website)

    def load_resource(self, path):
        """Given an URL path, return a Resource instance.
        """
        return self.GET(path=path, return_after='get_resource_for_request', want='resource')

    def get_session(self):
        s = StatefulClient(www_root=self.www_root, project_root=self.project_root)
        s._website = self._website
        return s

    # HTTP Methods (RFC 2616)
    # ============

    def GET(self, *a, **kw):
        return self.hit('GET', *a, **kw)

    def POST(self, *a, **kw):
        return self.hit('POST', *a, **kw)

    def OPTIONS(self, *a, **kw):
        return self.hit('OPTIONS', *a, **kw)

    def HEAD(self, *a, **kw):
        return self.hit('HEAD', *a, **kw)

    def PUT(self, *a, **kw):
        return self.hit('PUT', *a, **kw)

    def DELETE(self, *a, **kw):
        return self.hit('DELETE', *a, **kw)

    def TRACE(self, *a, **kw):
        return self.hit('TRACE', *a, **kw)

    def CONNECT(self, *a, **kw):
        return self.hit('CONNECT', *a, **kw)

    def GxT(self, *a, **kw):
        return self.hxt('GET', *a, **kw)

    def PxST(self, *a, **kw):
        return self.hxt('POST', *a, **kw)

    def xPTIONS(self, *a, **kw):
        return self.hxt('OPTIONS', *a, **kw)

    def HxAD(self, *a, **kw):
        return self.hxt('HEAD', *a, **kw)

    def PxT(self, *a, **kw):
        return self.hxt('PUT', *a, **kw)

    def DxLETE(self, *a, **kw):
        return self.hxt('DELETE', *a, **kw)

    def TRxCE(self, *a, **kw):
        return self.hxt('TRACE', *a, **kw)

    def CxNNECT(self, *a, **kw):
        return self.hxt('CONNECT', *a, **kw)

    def hxt(self, *a, **kw):
        try:
            self.hit(*a, **kw)
        except Response as response:
            return response
        else:
            raise DidntRaiseResponse

    def hit(self, method, path='/', body=None, data=None, content_type=None,
            raise_immediately=True, return_after=None, want='response', **headers):

        if data is not None:
            warnings.warn(DeprecationWarning(
                "The `data` argument is deprecated, please use `body` instead."
            ))
            body = data
        if isinstance(content_type, str):
            content_type = content_type.encode('ascii')
        if isinstance(body, (dict, list)):
            if content_type is None:
                content_type = MULTIPART_CONTENT
            if content_type.startswith(b'multipart/form-data'):
                body = encode_multipart(BOUNDARY, body)
            else:
                raise ValueError(f"Unknown `content_type`: {content_type!r}")

        environ = self.build_wsgi_environ(method, path, body, content_type, **headers)
        state = self.website.respond(
            environ,
            raise_immediately=raise_immediately,
            return_after=return_after,
        )

        return self.resolve_want(state, want)

    @staticmethod
    def resolve_want(state, want):
        attr_path = want.split('.')
        base = attr_path[0]
        attr_path = attr_path[1:]

        out = state[base]
        for name in attr_path:
            out = getattr(out, name)

        return out

    def build_wsgi_environ(self, method, url, body=None, content_type=None, cookies=None, **kw):
        # NOTE that in Pando (request.py make_franken_headers) only headers
        # beginning with ``HTTP`` are included in the request - and those are
        # changed to no longer include ``HTTP``. There are currently 2
        # exceptions to this: ``'CONTENT_TYPE'``, ``'CONTENT_LENGTH'`` which
        # are explicitly checked for.

        if isinstance(cookies, dict) and not isinstance(cookies, SimpleCookie):
            cookies, d = SimpleCookie(), cookies
            for k, v in d.items():
                cookies[str(k)] = str(v)

        typecheck(
            url, (bytes, str),
            method, str,
            content_type, (bytes, None),
            body, (bytes, None),
        )
        url = url.encode('ascii') if type(url) != bytes else url
        if b'?' in url:
            path, qs = url.split(b'?', 1)
        else:
            path, qs = url, None

        environ = {}
        if content_type is not None:
            environ[b'CONTENT_TYPE'] = content_type
        if cookies is not None:
            environ[b'HTTP_COOKIE'] = cookies.output(header='', sep='; ')
        environ[b'HTTP_HOST'] = b'localhost'
        if path:
            environ[b'PATH_INFO'] = path
        if qs:
            environ[b'QUERY_STRING'] = qs
        environ[b'REMOTE_ADDR'] = b'0.0.0.0'
        environ[b'REQUEST_METHOD'] = method.encode('ascii')
        environ[b'SERVER_PROTOCOL'] = b'HTTP/1.1'
        if body is not None:
            environ[b'wsgi.input'] = BytesIO(body)
            environ[b'HTTP_CONTENT_LENGTH'] = str(len(body)).encode('ascii')
        environ[b'wsgi.url_scheme'] = 'https'
        environ.update((k.encode('ascii'), v) for k, v in kw.items())
        return environ


class StatefulClient(Client):
    """This is a Client subclass that keeps cookies between calls."""

    def __init__(self, *a, **kw):
        super(StatefulClient, self).__init__(*a, **kw)
        self.cookie = SimpleCookie()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.cookie.clear()

    def hit(self, *a, **kw):
        cookies = kw.pop('cookies', None)
        if cookies:
            cookie = SimpleCookie()
            # session cookies first
            cookie.update(self.cookie)
            # request cookies second
            if isinstance(cookies, SimpleCookie):
                cookie.update(cookies)
            else:
                for k, v in cookies.items():
                    cookie[str(k)] = str(v)
        else:
            cookie = self.cookie
        kw['cookies'] = cookie

        want = kw.pop('want', 'response')
        kw['want'] = 'state'
        state = super(StatefulClient, self).hit(*a, **kw)
        r = state.get('response')
        if isinstance(r, Response) and r.headers.cookie:
            self.cookie.update(r.headers.cookie)

        return self.resolve_want(state, want)
