"""
:mod:`request`
--------------

Define a Request class and child classes.

Here is how we analyze the structure of an HTTP message, along with the objects
we use to model each::

    - request                   Request
        - line                  Line
            - method            Method      ASCII
            - uri               URI
                - path          Path
                  - parts       list of PathPart
                - querystring   Querystring
            - version           Version     ASCII
        - headers               Headers     str
            - cookie            Cookie      str
            - host              unicode     str
            - scheme            unicode     str
        - body                  Body        Content-Type?

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import re
import string
import sys
import traceback

from six import PY2

from aspen.http.request import Path as _Path, Querystring as _Querystring

from .. import Response
from ..exceptions import MalformedBody, UnknownBodyType
from ..urlparse import quote, quote_plus
from ..utils import try_encode
from .baseheaders import BaseHeaders
from .mapping import Mapping


# WSGI Do Our Best
# ================
# Pando is jealous. It wants to pretend that it parsed the HTTP Request itself,
# instead of letting some WSGI server or library do the work for it. Here are
# routines for going from WSGI back to HTTP. Since WSGI is lossy, we end up
# with a Dr. Frankenstein's HTTP message.

def make_franken_uri(path, qs):
    """Given two bytestrings, return a bytestring.

    We want to pass ASCII to Request. However, our friendly neighborhood WSGI
    servers do friendly neighborhood things with the Request-URI to compute
    PATH_INFO and QUERY_STRING. In addition, our friendly neighborhood browser
    sends "raw, unescaped UTF-8 bytes in the query during an HTTP request"
    (http://web.lookout.net/2012/03/unicode-normalization-in-urls.html).

    Our strategy is to try decoding to ASCII, and if that fails (we don't have
    ASCII) then we'll quote the value before passing to Request. What encoding
    are those bytes? Good question. The above blog post claims that experiment
    reveals all browsers to send UTF-8, so let's go with that? BUT WHAT ABOUT
    MAXTHON?!?!?!.

    """
    if path:
        # Some servers (gevent) clobber %2F inside of paths, such
        # that we see /foo%2Fbar/ as /foo/bar/. The %2F is lost to us.
        path = quote(path).encode('ascii')

    if qs:
        qs = b'?' + quote_plus(qs, '=&').encode('ascii')

    return path + qs


def make_franken_headers(environ):
    """Takes a WSGI environ, returns a dict of HTTP headers.

    https://www.python.org/dev/peps/pep-3333/#environ-variables
    """
    headers = [(k[5:], v) for k, v in environ.items() if k[:5] == b'HTTP_']
    headers.extend(
        (k, environ.get(k, None)) for k in (b'CONTENT_TYPE', b'CONTENT_LENGTH')
    )
    return dict((k.replace(b'_', b'-'), v) for k, v in headers if v is not None)


def kick_against_goad(environ):
    """Kick against the goad. Try to squeeze blood from a stone. Do our best.
    """
    method = environ[b'REQUEST_METHOD']
    uri = make_franken_uri( environ.get(b'PATH_INFO', b'')
                          , environ.get(b'QUERY_STRING', b'')
                          )
    server = environ.get(b'SERVER_SOFTWARE', b'')
    version = environ[b'SERVER_PROTOCOL']
    headers = make_franken_headers(environ)
    body = environ[b'wsgi.input']
    return method, uri, server, version, headers, body


###########
# Request #
###########

class Request(object):
    """Represent an HTTP Request message.

    .. attribute:: line

        See :class:`.Line`.

    .. attribute:: headers

        A mapping of HTTP headers. See :class:`.Headers`.

    """

    def __init__(self, website, method=b'GET', uri=b'/', server_software=b'',
                version=b'HTTP/1.1', headers=b'', body=None):
        """``body`` is expected to be a file-like object.
        """
        self.website = website
        self.server_software = server_software
        self.body_stream = body
        self.line = Line(method, uri, version)
        if not headers:
            headers = b'Host: localhost'
        self.headers = Headers(headers)

    @classmethod
    def from_wsgi(cls, website, environ):
        """Given a WSGI environ, return a new instance of the class.

        The conversion from HTTP to WSGI is lossy. This method does its best to
        go the other direction, but we can't guarantee that we've reconstructed
        the bytes as they were on the wire.

        Almost all the keys and values in a WSGI environ dict are (supposed to
        be) of type `str`, meaning bytestrings in python 2 and unicode strings
        in python 3. In this function we normalize them to bytestrings.
        Ref: https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types

        """
        environ = {try_encode(k): try_encode(v) for k, v in environ.items()}
        try:
            return cls(website, *kick_against_goad(environ))
        except UnicodeError as e:
            if website.show_tracebacks:
                msg = traceback.format_exc()
            else:
                tb = sys.exc_info()[2]
                while tb.tb_next is not None:
                    tb = tb.tb_next
                frame = tb.tb_frame
                filename = tb.tb_frame.f_code.co_filename
                msg = "Request is undecodable: %s (%s:%d)" % (e, filename, frame.f_lineno)
            raise Response(400, msg)

    # Aliases
    # =======

    @property
    def method(self):
        return self.line.method.as_text

    @property
    def path(self):
        return self.line.uri.path.mapping

    @property
    def qs(self):
        return self.line.uri.querystring.mapping

    @property
    def cookie(self):
        return self.headers.cookie

    @property
    def content_length(self):
        """This property attempts to parse the ``Content-Length`` header.

        Returns zero if the header is missing or empty.

        Raises a 400 :class:`.Response` if the header is not a valid integer.
        """
        cl = self.headers.get(b'Content-Length') or b'0'
        try:
            return int(cl)
        except ValueError:
            safe = cl.decode('ascii', 'backslashreplace')
            raise Response(400, "Content-Length is not a valid integer: %s" % safe)

    @property
    def body_bytes(self):
        """Lazily read the whole request body.

        Returns ``b''`` if the request doesn't have a body.
        """
        if self.body_stream is None:
            return b''
        if hasattr(self, '_body_bytes'):
            return self._body_bytes
        self._body_bytes = self.body_stream.read(self.content_length)
        return self._body_bytes

    @property
    def body(self):
        """This property calls :meth:`parse_body()` and caches the result.
        """
        if hasattr(self, 'parsed_body'):
            return self.parsed_body
        self.parsed_body = self.parse_body()
        return self.parsed_body

    @body.setter
    def body(self, value):
        """Let the developer set the body to something if they want"""
        self.parsed_body = value

    def parse_body(self):
        """Parses :attr:`body_bytes` using :attr:`headers` to determine which of
        the :attr:`~pando.website.Website.body_parsers` should be used.

        Raises :exc:`.UnknownBodyType` if the HTTP ``Content-Type`` isn't
        recognized, and :exc:`.MalformedBody` if the parsing fails.

        """

        raw = self.body_bytes

        # Note we ignore parameters for now
        content_type = self.headers.get(b"Content-Type", b"").split(b';')[0]
        content_type = content_type.decode('ascii', 'backslashreplace')

        def default_parser(raw, headers):
            if not content_type and not raw:
                return {}
            raise UnknownBodyType(content_type)

        parser = self.website.body_parsers.get(content_type, default_parser)
        try:
            return parser(raw, self.headers)
        except ValueError as e:
            raise MalformedBody(str(e))

    # Special methods
    # ===============

    def __str__(self):
        """Lazily load the body and return the whole message.

        When working with a Request object interactively or in a debugging
        situation we want it to behave transparently string-like. We don't want
        to read bytes off the wire if we can avoid it, though, because for mega
        file uploads and such this could have a big impact.
        """
        bs = (
            self.line + b'\r\n' +
            self.headers.raw + b'\r\n\r\n' +
            self.body_bytes
        )
        return bs if PY2 else bs.decode('ascii')

    def __repr__(self):
        return str.__repr__(str(self))

    def __cmp__(self, other):
        return str.__cmp__(str(self), other)

    # Public Methods
    # ==============

    def allow(self, *methods):
        """Given method strings, raise 405 if ours is not among them.

        The method names are case insensitive (they are uppercased). If 405
        is raised then the Allow header is set to the methods given.

        """
        methods = [x.upper() for x in methods]
        if self.method not in methods:
            raise Response(405, headers={
                b'Allow': b', '.join(m.encode('ascii') for m in methods)
            })

    def is_xhr(self):
        """Check the value of X-Requested-With.
        """
        val = self.headers.get(b'X-Requested-With', b'')
        return val.lower() == b'xmlhttprequest'


# Request -> Line
# ---------------

class Line(bytes):
    """Represent the first line of an HTTP Request message.
    """

    def __new__(cls, method, uri, version):
        """Takes three bytestrings.
        """
        raw = b" ".join([method, uri, version])
        method = Method(method)
        uri = URI(uri)
        version = Version(version)

        obj = super(Line, cls).__new__(cls, raw)
        obj.method = method
        obj.uri = uri
        obj.version = version
        return obj


# Request -> Method
# -----------------

STANDARD_METHODS = set("OPTIONS GET HEAD POST PUT DELETE TRACE CONNECT".split())
"""A set containing the 8 basic HTTP methods.

If your application uses other standard methods (see the `HTTP Method Registry
<http://www.iana.org/assignments/http-methods/http-methods.xhtml>`_), or custom
methods, you can add them to this set to improve performance.
"""

CHARS_ALLOWED_IN_METHOD = set(
    string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~"
)

class Method(bytes):
    """Represent the HTTP method in the first line of an HTTP Request message.
    """

    def __new__(cls, raw):
        """Creates a new Method object.

        Raises a 400 :class:`.Response` if the given bytestring is not a
        valid HTTP method, per RFC7230 section 3.1.1:

            Recipients of an invalid request-line SHOULD respond with either a
            400 (Bad Request) error or a 301 (Moved Permanently) redirect with
            the request-target properly encoded.

        `RFC7230 <https://tools.ietf.org/html/rfc7230>`_ defines valid methods as::

            method         = token

            token          = 1*tchar

            tchar          = "!" / "#" / "$" / "%" / "&" / "'" / "*"
                           / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
                           / DIGIT / ALPHA
                           ; any VCHAR, except delimiters

        """
        decoded = raw.decode('ascii', 'backslashreplace')
        if decoded not in STANDARD_METHODS: # fast for 99.999% case
            if any(char not in CHARS_ALLOWED_IN_METHOD for char in decoded):
                raise Response(400, "Your request method violates RFC 7230: %s" % decoded)

        obj = super(Method, cls).__new__(cls, raw)
        obj.as_text = decoded
        return obj


# Request -> Line -> URI
# ......................

class URI(bytes):
    """Represent the Request-URI in the first line of an HTTP Request message.
    """

    def __new__(cls, raw):
        """Creates a URI object from a raw bytestring.

        We require that ``raw`` be decodable with ASCII, if it isn't a 400
        :class:`Response` is raised.
        """
        parts = raw.split(b'?', 1)
        path = Path(parts[0])
        querystring = Querystring(parts[1] if len(parts) > 1 else b'')
        decoded = path.decoded
        if len(parts) > 1:
            decoded += '?' + querystring.decoded
        obj = super(URI, cls).__new__(cls, raw)
        obj.path = path
        obj.querystring = querystring
        obj.decoded = decoded
        return obj


# Request -> Line -> URI -> Path

class Path(bytes):
    """
    .. attribute:: decoded

        The path decoded to text.

    .. attribute:: mapping

        :class:`.Mapping` of path variables.

    .. attribute:: parts

        List of :class:`~aspen.http.request.PathPart` instances.
    """

    def __new__(cls, raw):
        """Creates a Path object from a raw bytestring.
        """
        try:
            decoded = raw.decode('ascii')
        except UnicodeError:
            safe = raw.decode('ascii', 'backslashreplace')
            raise Response(400, "Request path isn't ascii: %s" % safe)
        mapping = _PathMapping(decoded)
        obj = super(Path, cls).__new__(cls, raw)
        obj.decoded = decoded
        obj.mapping = mapping
        obj.parts = mapping.parts
        return obj


class _PathMapping(Mapping, _Path):
    pass


# Request -> Line -> URI -> Querystring

class Querystring(bytes):
    """
    .. attribute:: decoded

        The querystring decoded to text.

    .. attribute:: mapping

        :class:`.Mapping` of querystring variables.
    """

    def __new__(cls, raw):
        """Creates a Querystring object from a raw bytestring.
        """
        try:
            decoded = raw.decode('ascii')
        except UnicodeError:
            safe = raw.decode('ascii', 'backslashreplace')
            raise Response(400, "Request querystring isn't ascii: %s" % safe)
        mapping = _QuerystringMapping(decoded)
        obj = super(Querystring, cls).__new__(cls, raw)
        obj.decoded = decoded
        obj.mapping = mapping
        return obj


class _QuerystringMapping(Mapping, _Querystring):
    pass


# Request -> Line -> Version
# ..........................

versions = { b'HTTP/0.9': (0, 9)
           , b'HTTP/1.0': (1, 0)
           , b'HTTP/1.1': (1, 1)
            }

version_re = re.compile(br'^HTTP/([0-9])\.([0-9])$')

class Version(bytes):
    """Holds the version from the HTTP status line, e.g. HTTP/1.1.

    Accessing the :attr:`info`, :attr:`major`, or :attr:`minor`
    attribute will raise a 400 :class:`.Response` if the version is invalid.

    `RFC7230 section 2.6 <https://tools.ietf.org/html/rfc7230#section-2.6>`_::

        HTTP-version  = HTTP-name "/" DIGIT "." DIGIT
        HTTP-name     = %x48.54.54.50 ; "HTTP", case-sensitive

    """

    __slots__ = []

    @property
    def info(self):
        version = versions.get(self, None)
        if version is not None:  # fast for 99.999999% case
            return version
        else:
            safe = self.safe_decode()
            m = version_re.match(self)
            if m is None:
                raise Response(400, "Bad HTTP version: %s." % safe)
            return int(m.group(1)), int(m.group(2))

    @property
    def major(self):
        return self.info[0]

    @property
    def minor(self):
        return self.info[1]

    def safe_decode(self):
        return self.decode('ascii', 'backslashreplace')


# Request -> Headers
# ------------------

class Headers(BaseHeaders):
    """Model headers in an HTTP Request message.
    """

    def __init__(self, raw):
        """Extend BaseHeaders to add extra attributes.
        """
        BaseHeaders.__init__(self, raw)


        # Host
        # ====
        # Per the spec, respond with 400 if no Host header is given. However,
        # we prefer X-Forwarded-For if that is available.

        host = self.get(b'X-Forwarded-Host', self[b'Host']) # KeyError raises 400
        try:
            self.host = host.decode('idna')
        except UnicodeError:
            self.host = ''


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        scheme = 'https' if self.get('HTTPS', False) else 'http'
        self.scheme = scheme
