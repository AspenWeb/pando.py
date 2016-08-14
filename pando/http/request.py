"""
pando.http.request
~~~~~~~~~~~~~~~~~~

Define a Request class and child classes.

Here is how we analyze the structure of an HTTP message, along with the objects
we use to model each:

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


XXX TODO
    make URI conform to spec (path, querystring)
    test franken*
    validate Mapping
    clean up headers
    clean up body

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from io import BytesIO
import re
import sys

from six import PY2, text_type
import six.moves.urllib.parse as urlparse

from aspen.http.request import Path as _Path, Querystring as _Querystring

from .. import Response
from ..utils import maybe_encode
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
        """Given a WSGI environ, return an instance of cls.

        The conversion from HTTP to WSGI is lossy. This method does its best to
        go the other direction, but we can't guarantee that we've reconstructed
        the bytes as they were on the wire (which is what I want). It would
        also be more efficient to parse directly for our API. But people love
        their gunicorn. :-/

        Almost all the keys and values in a WSGI environ dict are (supposed to
        be) of type `str`, meaning bytestrings in python 2 and unicode strings
        in python 3. In this function we normalize them to bytestrings.
        Ref: https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types

        """
        environ = {maybe_encode(k): maybe_encode(v) for k, v in environ.items()}
        return cls(*kick_against_goad(environ))


    # Set up some aliases.
    # ====================

    @property
    def method(self):
        return self.line.method

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
        '''Lazily parse the body, iff _parse_body is set.
           Otherwise default to raw_body.  In the normal course of things,
           _parse_body is set in pando.algorithm.website
        '''
        if hasattr(self, 'parsed_body'):
            return self.parsed_body
        if hasattr(self, '_parse_body'):
            self.parsed_body = self._parse_body(self)
            return self.parsed_body
        return self.raw_body

    @body.setter
    def body(self, value):
        '''Let the developer set the body to something if they want'''
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
            fmt = b"%s\r\n%s\r\n\r\n%s"
            bs = fmt % (self.line.raw, self.headers.raw, self.raw_body)
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
        if self.line.method not in methods:
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

class Line(text_type):
    """Represent the first line of an HTTP Request message.
    """

    __slots__ = ['method', 'uri', 'version', 'raw']

    def __new__(cls, method, uri, version):
        """Takes three bytestrings.
        """
        raw = b" ".join([method, uri, version])
        method = Method(method)
        uri = URI(uri)
        version = Version(version)
        decoded = " ".join([method, uri, version])

        obj = super(Line, cls).__new__(cls, decoded)
        obj.method = method
        obj.uri = uri
        obj.version = version
        obj.raw = raw
        return obj



# Request -> Method
# -----------------

STANDARD_METHODS = set("OPTIONS GET HEAD POST PUT DELETE TRACE CONNECT".split())

SEPARATORS = ("(", ")", "<", ">", "@", ",", ";", ":", "\\", '"', "/", "[", "]",
              "?", "=", "{", "}", " ", "\t")

CHARS_ALLOWED_IN_METHOD = set(chr(i) for i in range(32, 127)) - set(SEPARATORS)

class Method(text_type):
    """Represent the HTTP method in the first line of an HTTP Request message.

    Spec sez ASCII subset:

        Method         = "OPTIONS"                ; Section 9.2
                       | "GET"                    ; Section 9.3
                       | "HEAD"                   ; Section 9.4
                       | "POST"                   ; Section 9.5
                       | "PUT"                    ; Section 9.6
                       | "DELETE"                 ; Section 9.7
                       | "TRACE"                  ; Section 9.8
                       | "CONNECT"                ; Section 9.9
                       | extension-method
        extension-method = token

        (http://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5.1.1)


        CHAR           = <any US-ASCII character (octets 0 - 127)>
        ...
        CTL            = <any US-ASCII control character
                         (octets 0 - 31) and DEL (127)>
        ...
        SP             = <US-ASCII SP, space (32)>
        HT             = <US-ASCII HT, horizontal-tab (9)>
        ...
        token          = 1*<any CHAR except CTLs or separators>
        separators     = "(" | ")" | "<" | ">" | "@"
                       | "," | ";" | ":" | "\" | <">
                       | "/" | "[" | "]" | "?" | "="
                       | "{" | "}" | SP | HT

        (http://www.w3.org/Protocols/rfc2616/rfc2616-sec2.html#sec2.2)

    """

    __slots__ = ['raw']

    def __new__(cls, raw):
        decoded = raw.decode('ascii', 'repr')
        if decoded not in STANDARD_METHODS: # fast for 99.999% case
            for i, char in enumerate(decoded):
                if (i == 64) or (char not in CHARS_ALLOWED_IN_METHOD):

                    # "This is the appropriate response when the server does
                    #  not recognize the request method and is not capable of
                    #  supporting it for any resource."
                    #
                    #  http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

                    raise Response(501, "Your request-method violates RFC "
                                        "2616: %s" % decoded)

        obj = super(Method, cls).__new__(cls, decoded)
        obj.raw = raw
        return obj


# Request -> Line -> URI
# ......................

class URI(text_type):
    """Represent the Request-URI in the first line of an HTTP Request message.

    XXX spec-ify this

    """

    __slots__ = ['path', 'querystring', 'raw']

    def __new__(cls, raw):
        # we require that the uri as a whole be decodable with ASCII
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

versions = { b'HTTP/0.9': ((0, 9), 'HTTP/0.9')
           , b'HTTP/1.0': ((1, 0), 'HTTP/1.0')
           , b'HTTP/1.1': ((1, 1), 'HTTP/1.1')
            }  # Go ahead, find me another version.

version_re = re.compile(br'HTTP/\d+\.\d+')

class Version(text_type):
    """Represent the version in an HTTP status line. HTTP/1.1. Like that.

        HTTP-Version   = "HTTP" "/" 1*DIGIT "." 1*DIGIT

        (http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html)

    """

    __slots__ = ['major', 'minor', 'info', 'raw']

    def __new__(cls, raw):
        version = versions.get(raw, None)
        if version is None: # fast for 99.999999% case
            safe = raw.decode('ascii', 'repr')
            if version_re.match(raw) is None:
                raise Response(400, "Bad HTTP version: %s." % safe)
            else:
                raise Response(505, "HTTP Version Not Supported: %s. This "
                                    "server supports HTTP/0.9, HTTP/1.0, and "
                                    "HTTP/1.1." % safe)
        version, decoded = version

        obj = super(Version, cls).__new__(cls, decoded)
        obj.major = version[0]  # 1
        obj.minor = version[1]  # 1
        obj.info = version      # (1, 1)
        obj.raw = raw           # 'HTTP/1.1'
        return obj


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
