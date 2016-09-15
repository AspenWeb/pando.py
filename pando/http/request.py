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


from io import BytesIO
import re
import string
import sys

from six import PY2, text_type
import six.moves.urllib.parse as urlparse

from aspen.http.request import Path as _Path, Querystring as _Querystring

from .. import Response
from ..utils import try_encode
from .baseheaders import BaseHeaders
from .mapping import Mapping


# WSGI Do Our Best
# ================
# Pando is jealous. It wants to pretend that it parsed the HTTP Request itself,
# instead of letting some WSGI server or library do the work for it. Here are
# routines for going from WSGI back to HTTP. Since WSGI is lossy, we end up
# with a Dr. Frankenstein's HTTP message.

quoted_slash_re = re.compile("%2F", re.IGNORECASE)


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
        try:
            path.decode('ASCII')    # NB: We throw away this unicode!
        except UnicodeDecodeError:

            # XXX How would we get non-ASCII here? The lookout.net post
            # indicates that all browsers send ASCII for the path.

            # Some servers (gevent) clobber %2F inside of paths, such
            # that we see /foo%2Fbar/ as /foo/bar/. The %2F is lost to us.
            parts = [urlparse.quote(x) for x in quoted_slash_re.split(path)]
            path = b"%2F".join(parts)

    if qs:
        try:
            qs.decode('ASCII')      # NB: We throw away this unicode!
        except UnicodeDecodeError:
            # Cross our fingers and hope we have UTF-8 bytes from MSIE. Let's
            # perform the percent-encoding that we would expect MSIE to have
            # done for us.
            qs = urlparse.quote_plus(qs)
        qs = b'?' + qs

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


# *WithRaw
# ========
# A few parts of the Request object model use these generic objects.

class IntWithRaw(int):
    """Generic subclass of int to store the underlying raw bytestring.
    """

    def __new__(cls, i):
        if i is None:
            i = 0
        obj = super(IntWithRaw, cls).__new__(cls, i)
        obj.raw = str(i)
        return obj

class UnicodeWithRaw(text_type):
    """Generic subclass of unicode to store the underlying raw bytestring.
    """

    __slots__ = ['raw']

    def __new__(cls, raw, encoding='UTF-8'):
        obj = super(UnicodeWithRaw, cls).__new__(cls, raw.decode(encoding))
        obj.raw = raw
        return obj


###########
# Request #
###########

class Request(str):
    """Represent an HTTP Request message. It's bytes, dammit. But lazy.
    """

    resource = None
    original_resource = None
    server_software = ''

    # NB: no __slots__ for str:
    #   http://docs.python.org/reference/datamodel.html#__slots__


    def __new__(cls, method=b'GET', uri=b'/', server_software=b'',
                version=b'HTTP/1.1', headers=b'', body=None):
        """Takes five bytestrings and a file-like object.
        """
        obj = str.__new__(cls, '') # start with an empty string, see below for
                                   # laziness
        obj.server_software = server_software
        try:
            obj.line = Line(method, uri, version)
            if not headers:
                headers = b'Host: localhost'
            obj.headers = Headers(headers)
            if body is None:
                body = BytesIO(b'')
            raw_len = int(obj.headers.get(b'Content-length', b'') or b'0')
            obj.raw_body = body.read(raw_len)
            obj.context = {}
        except UnicodeError:
            # Figure out where the error occurred.
            # ====================================
            # This gives us *something* to go on when we have a Request we
            # can't parse. XXX Make this more nicer. That will require wrapping
            # every point in Request parsing where we decode bytes.

            tb = sys.exc_info()[2]
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            filename = tb.tb_frame.f_code.co_filename

            raise Response(400, "Request is undecodable. "
                                "(%s:%d)" % (filename, frame.f_lineno))

        return obj


    @classmethod
    def from_wsgi(cls, environ):
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
        return cls(*kick_against_goad(environ))


    # Set up some aliases.
    # ====================

    @property
    def method(self):
        return self.line.method.as_text

    @property
    def path(self):
        return self.line.uri.path

    @property
    def qs(self):
        return self.line.uri.querystring

    @property
    def cookie(self):
        return self.headers.cookie

    @property
    def body(self):
        """Lazily parse the body.

        If we don't have a parser that matches the request's ``Content-Type``,
        then the raw body is returned as a bytestring.
        """
        if hasattr(self, 'parsed_body'):
            return self.parsed_body
        # In the normal course of things, _parse_body is set by parse_body_into_request()
        if hasattr(self, '_parse_body'):
            self.parsed_body = self._parse_body(self)
            return self.parsed_body
        return self.raw_body

    @body.setter
    def body(self, value):
        """Let the developer set the body to something if they want"""
        self.parsed_body = value


    # Extend str to lazily load bytes.
    # ================================
    # When working with a Request object interactively or in a debugging
    # situation we want it to behave transparently string-like. We don't want
    # to read bytes off the wire if we can avoid it, though, because for mega
    # file uploads and such this could have a big impact.

    _raw = "" # XXX We should reset this when subobjects are mutated.
    def __str__(self):
        """Lazily load the body and return the whole message.
        """
        if not self._raw:
            bs = (
                self.line + b'\r\n' +
                self.headers.raw + b'\r\n\r\n' +
                self.raw_body
            )
            self._raw = bs if PY2 else bs.decode('ascii')
        return self._raw

    def __repr__(self):
        return str.__repr__(str(self))

    # str defines rich comparisons, so we have to extend those and not simply
    # __cmp__ (http://docs.python.org/reference/datamodel.html#object.__lt__)

    def __lt__(self, other): return str.__lt__(str(self), other)
    def __le__(self, other): return str.__le__(str(self), other)
    def __eq__(self, other): return str.__eq__(str(self), other)
    def __ne__(self, other): return str.__ne__(str(self), other)
    def __gt__(self, other): return str.__gt__(str(self), other)
    def __ge__(self, other): return str.__ge__(str(self), other)


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

        Raises a 400 :py:class:`.Response` if the given bytestring is not a
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
        decoded = raw.decode('ascii', 'repr')
        if decoded not in STANDARD_METHODS: # fast for 99.999% case
            if any(char not in CHARS_ALLOWED_IN_METHOD for char in decoded):
                raise Response(400, "Your request method violates RFC 7230: %s" % decoded)

        obj = super(Method, cls).__new__(cls, raw)
        obj.as_text = decoded
        return obj


# Request -> Line -> URI
# ......................

class URI(text_type):
    """Represent the Request-URI in the first line of an HTTP Request message.
    """

    __slots__ = ['path', 'querystring', 'raw']

    def __new__(cls, raw):
        """Creates a URI object from a raw bytestring.

        We require that ``raw`` be decodable with ASCII, if it isn't a
        :py:exc:`UnicodeDecodeError` is raised.
        """
        decoded = raw.decode('ASCII')
        parts = decoded.split('?', 1)
        path = Path(parts[0])
        querystring = Querystring(parts[1] if len(parts) > 1 else '')
        obj = super(URI, cls).__new__(cls, decoded)
        obj.path = path
        obj.querystring = querystring
        obj.raw = raw
        return obj


# Request -> Line -> URI -> Path

class Path(Mapping, _Path):
    pass


# Request -> Line -> URI -> Querystring

class Querystring(Mapping, _Querystring):
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

    Accessing the :py:attr:`info`, :py:attr:`major`, or :py:attr:`minor`
    attribute will raise a 400 :py:class:`.Response` if the version is invalid.

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
        return self.decode('ascii', 'repr')


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
        self.host = UnicodeWithRaw(host, encoding='idna')


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        scheme = 'https' if self.get('HTTPS', False) else 'http'
        self.scheme = scheme
