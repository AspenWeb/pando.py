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
        - body                  Body        Content-Type?

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ipaddress import ip_address
import re
import string
import sys
import traceback
import warnings

from six import PY2

from aspen.http.request import Path as _Path, Querystring as _Querystring

from .. import Response
from ..exceptions import MalformedBody, UnknownBodyType
from ..urlparse import quote, quote_plus
from ..utils import maybe_encode
from .baseheaders import BaseHeaders as Headers
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
        try:
            path.decode('ASCII')    # NB: We throw away this unicode!
        except UnicodeDecodeError:
            # Either the client sent unescaped non-ASCII bytes, or the web server
            # unescaped the path.
            path = quote(path, string.punctuation).encode('ASCII')

    if qs:
        try:
            qs.decode('ASCII')      # NB: We throw away this unicode!
        except UnicodeDecodeError:
            # Either the client sent unescaped non-ASCII bytes, or the web server
            # unescaped the query.
            qs = quote_plus(qs, string.punctuation).encode('ASCII')
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
    body = environ.get(b'wsgi.input')
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
                version=b'HTTP/1.1', headers={b'Host': b'localhost'}, body=None):
        """``body`` is expected to be a file-like object.
        """
        self.website = website
        self.server_software = server_software
        self.body_stream = body
        self.line = Line(method, uri, version)
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
        try:
            environ = {
                maybe_encode(k, 'latin1'): maybe_encode(v, 'latin1')
                for k, v in environ.items()
            }
            r = cls(website, *kick_against_goad(environ))
            r.environ = environ
            return r
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

    # Body handling
    # =============

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
            raise Response(400,
                "The 'Content-Length' header is not a valid integer: %s" % safe
            )

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
                return Mapping()
            raise UnknownBodyType(content_type)

        parser = self.website.body_parsers.get(content_type, default_parser)
        try:
            return parser(raw, self.headers)
        except ValueError as e:
            raise MalformedBody(str(e))

    # Other properties
    # ================

    @property
    def host(self):
        """The hostname of the request.

        Raises a 400 :class:`.Response` if no ``Host`` header is found or if
        decoding it fails. See
        `RFC7230 section 5.4 <https://tools.ietf.org/html/rfc7230#section-5.4>`_.
        """
        host = self.headers[b'Host']
        try:
            return host.decode('idna')
        except UnicodeError:
            raise Response(400,
                "The 'Host' header is not a valid domain name: %r" % host
            )

    @property
    def scheme(self):
        """The guessed URL scheme of the request, usually 'https' or 'http'.

        If the ``website.trusted_proxies`` list is empty, then the value of the
        `WSGI`_ variable ``url_scheme`` is returned, otherwise the value of the
        `X-Forwarded-Proto`_ HTTP header is returned.

        Support for `RFC7239 <https://tools.ietf.org/html/rfc7239>`_ may be
        added in the future (patches welcome ;-)).

        If the scheme cannot be determined or isn't in
        :attr:`~pando.website.DefaultConfiguration.known_schemes`,
        then a :class:`Warning` is emitted and 'https' is returned, because it's
        better to fail safely than to downgrade to an insecure connection.

        .. _WSGI:
            https://www.python.org/dev/peps/pep-3333/
        .. _X-Forwarded-Proto:
            https://developer.mozilla.org/docs/Web/HTTP/Headers/X-Forwarded-Proto
        """
        scheme = None
        if self.website.trusted_proxies or not self.environ.get(b'REMOTE_ADDR'):
            source = '`X-Forwarded-Proto` header'
            scheme = self.headers.get(b'X-Forwarded-Proto')
            if scheme:
                scheme = scheme.decode('ascii', 'backslashreplace')
        else:
            source = '`wsgi.url_scheme` variable'
            scheme = self.environ.get(b'wsgi.url_scheme')
            if scheme:
                scheme = scheme.decode('ascii', 'backslashreplace')
        if scheme in self.website.known_schemes:
            return scheme
        elif not scheme:
            warnings.warn("The %s is missing or empty." % source)
        else:
            warnings.warn("The %s value isn't a known scheme: %r" % (source, scheme))
        return 'https'

    @property
    def source(self):
        """The IP address of the client (an :class:`~ipaddress.IPv4Address` or
        :class:`~ipaddress.IPv6Address` object).

        This property looks at the WSGI ``REMOTE_ADDR`` variable and the HTTP
        ``X-Forwarded-For`` header, trusting only the proxies listed in
        :attr:`~pando.website.DefaultConfiguration.trusted_proxies`.

        .. warning::
            If the  :attr:`~pando.website.DefaultConfiguration.trusted_proxies`
            list is incorrect or incomplete, then this property can mistakenly
            return the IP address of a reverse proxy instead of the client's IP
            address.

        """
        r = self.__dict__.get('source')
        if r is not None:
            return r

        def f():
            addr = self.environ.get(b'REMOTE_ADDR')
            forwarded_for = self.headers.get(b'X-Forwarded-For', b'')
            if addr:
                addr = ip_address(addr.decode('ascii').strip())
            else:
                # The WSGI server didn't provide the client's IP address. This
                # probably means that it received the request through a Unix
                # socket.
                if forwarded_for:
                    i = forwarded_for.rfind(b',')
                    try:
                        addr = ip_address(forwarded_for[i+1:].decode('ascii').strip())
                    except (UnicodeDecodeError, ValueError):
                        safe = forwarded_for.decode('ascii', 'backslashreplace')
                        raise Response(400,
                            "The 'X-Forwarded-For' header value is invalid: " + safe
                        )
                    forwarded_for = forwarded_for[:i]
                else:
                    return
            trusted_proxies = self.website.trusted_proxies
            self.__dict__['bypasses_proxy'] = bool(trusted_proxies)
            if not trusted_proxies or not forwarded_for:
                return addr
            for networks in trusted_proxies:
                is_trusted = False
                for network in networks:
                    is_trusted = addr.is_private if network == 'private' else addr in network
                    if is_trusted:
                        break
                if not is_trusted:
                    return addr
                i = forwarded_for.rfind(b',')
                try:
                    addr = ip_address(forwarded_for[i+1:].decode('ascii').strip())
                except (UnicodeDecodeError, ValueError):
                    return addr
                if i == -1:
                    if networks is trusted_proxies[-1]:
                        break
                    return addr
                forwarded_for = forwarded_for[:i]
            self.__dict__['bypasses_proxy'] = False
            return addr

        r = f()
        self.__dict__['source'] = r
        return r

    @property
    def bypasses_proxy(self):
        """This property returns ``False`` if the request came through all the proxy
        levels listed in :attr:`~pando.website.DefaultConfiguration.trusted_proxies`,
        and ``True`` if the request bypassed at least one proxy level.
        """
        if 'bypasses_proxy' not in self.__dict__:
            # Call the `source` property to get the `bypasses_proxy` boolean.
            self.source
        return self.__dict__['bypasses_proxy']

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
    __init__ = _Path.__init__


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
    __init__ = _Querystring.__init__


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
