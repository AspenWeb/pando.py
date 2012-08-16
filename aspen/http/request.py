"""Define a Request class and child classes.

Here is how we analyze the structure of an HTTP message, along with the objects
we use to model each:

    - request                   Request
        - line                  Line
            - method            Method      ASCII
            - uri               URI
                - path          Path
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
import cgi
import mimetypes
import re
import sys
import urllib
import urlparse
from cStringIO import StringIO

from aspen import Response
from aspen.http.baseheaders import BaseHeaders
from aspen.http.mapping import Mapping
from aspen.context import Context
from aspen.utils import ascii_dammit, typecheck


# WSGI Do Our Best
# ================
# Aspen is jealous. It wants to pretend that it parsed the HTTP Request itself,
# instead of letting some WSGI server or library do the work for it. Here are
# routines for going from WSGI back to HTTP. Since WSGI is lossy, we end up
# with a Dr. Frankenstein's HTTP message.

quoted_slash_re = re.compile("%2F", re.IGNORECASE)


def make_franken_uri(path, querystr):
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
            path.decode('ASCII')
        except UnicodeDecodeError:
            # Some servers (gevent) clobber %2F inside of paths, such
            # that we see /foo%2Fbar/ as /foo/bar/. The %2F is lost to us.
            parts = [urllib.quote(x) for x in quoted_slash_re.split(path)]
            path = "%2F".join(parts)

    if querystr:
        try:
            querystr.decode('ASCII')
        except UnicodeDecodeError:
            # Cross our fingers and hope we have UTF-8 bytes from MSIE.
            querystr = urllib.quote_plus(querystr)
        querystr = '?' + querystr

    return path + querystr


def make_franken_headers(environ):
    """Takes a WSGI environ, returns a bytestring.
    """

    # There are a couple keys that CherryPyWSGIServer explicitly doesn't
    # include as HTTP_ keys. I'm not sure why, but I believe we want them.
    also = ['CONTENT_TYPE', 'CONTENT_LENGTH']

    headers = []
    for k, v in environ.items():
        val = None
        if k.startswith('HTTP_'):
            k = k[len('HTTP_'):]
            val = v
        elif k in also:
            val = v
        if val is not None:
            k = k.replace('_', '-')
            headers.append(': '.join([k, v]))

    return '\r\n'.join(headers)  # *sigh*


def kick_against_goad(environ):
    """Kick against the goad. Try to squeeze blood from a stone. Do our best.
    """
    method = environ['REQUEST_METHOD']
    uri = make_franken_uri( environ.get('PATH_INFO', '')
                          , environ.get('QUERY_STRING', '')
                           )
    server = environ.get('SERVER_SOFTWARE', '')
    version = environ['SERVER_PROTOCOL']
    headers = make_franken_headers(environ)
    body = environ['wsgi.input']
    return method, uri, server, version, headers, body


# *WithRaw
# ========
# A few parts of the Request object model use these generic objects.

class IntWithRaw(int):
    """Generic subclass of int to store the underlying raw bytestring.
    """

    __slots__ = ['raw']

    def __new__(cls, i):
        if i is None:
            i = 0
        obj = super(IntWithRaw, cls).__new__(cls, i)
        obj.raw = str(i)
        return obj

class UnicodeWithRaw(unicode):
    """Generic subclass of unicode to store the underlying raw bytestring.
    """

    __slots__ = ['raw']

    def __new__(cls, raw, encoding="UTF-8"):
        obj = super(UnicodeWithRaw, cls).__new__(cls, raw.decode(encoding))
        obj.raw = raw
        return obj


###########
# Request #
###########

class Request(str):
    """Represent an HTTP Request message. It's bytes, dammit. But lazy.
    """

    socket = None
    resource = None
    original_resource = None
    server_software = ''
    fs = '' # the file on the filesystem that will handle this request

    # NB: no __slots__ for str:
    #   http://docs.python.org/reference/datamodel.html#__slots__


    def __new__(cls, method='GET', uri='/', server_software='',
                version='HTTP/1.1', headers='', body=None):
        """Takes five bytestrings and an iterable of bytestrings.
        """
        obj = str.__new__(cls, '') # start with an empty string, see below for
                                   # laziness
        obj.server_software = server_software
        try:
            obj.line = Line(method, uri, version)
            if not headers:
                headers = 'Host: localhost'
            obj.headers = Headers(headers)
            if body is None:
                body = StringIO('')
            obj.body = Body( obj.headers
                           , body
                           , obj.server_software
                            )
            obj.context = Context(obj)
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

        """
        return cls(*kick_against_goad(environ))


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
            fmt = "%s\r\n%s\r\n\r\n%s"
            self._raw = fmt % (self.line.raw, self.headers.raw, self.body.raw)
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
            raise Response(405, headers={'Allow': ', '.join(methods)})

    def is_xhr(self):
        """Check the value of X-Requested-With.
        """
        val = self.headers.get('X-Requested-With', '')
        return val.lower() == 'xmlhttprequest'

    @staticmethod
    def redirect(location, code=None, permanent=False):
        """Given a string, an int, and a boolean, raise a Response.

        If code is None then it will be set to 301 (Moved Permanently) if
        permanent is True and 302 (Found) if it is False.

        XXX Some day port this:

            http://cherrypy.org/browser/trunk/cherrypy/_cperror.py#L154

        """
        if code is None:
            code = permanent is True and 301 or 302
        raise Response(code, headers={'Location': location})


    def _infer_media_type(self):
        """Guess a media type based on our filesystem path.

        The gauntlet function indirect_negotiation modifies the filesystem
        path, and we want to infer a media type from the path before that
        change. However, we're not ready at that point to infer a media type
        for *all* requests. So we need to perform this inference in a couple
        places, and hence it's factored out here.

        """
        media_type = mimetypes.guess_type(self.fs, strict=False)[0]
        if media_type is None:
            media_type = self.website.media_type_default
        return media_type

# Request -> Line
# ---------------

class Line(unicode):
    """Represent the first line of an HTTP Request message.
    """

    __slots__ = ['method', 'uri', 'version', 'raw']

    def __new__(cls, method, uri, version):
        """Takes three bytestrings.
        """
        raw = " ".join([method, uri, version])
        method = Method(method)
        uri = URI(uri)
        version = Version(version)
        decoded = u" ".join([method, uri, version])

        obj = super(Line, cls).__new__(cls, decoded)
        obj.method = method
        obj.uri = uri
        obj.version = version
        obj.raw = raw
        return obj



# Request -> Method
# -----------------

STANDARD_METHODS = set(["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE",
                    "CONNECT"])

SEPARATORS = ("(", ")", "<", ">", "@", ",", ";", ":", "\\", '"', "/", "[", "]",
              "?", "=", "{", "}", " ", "\t")

# NB: No set comprehensions until 2.7.
BYTES_ALLOWED_IN_METHOD = set(chr(i) for i in range(32, 127))
BYTES_ALLOWED_IN_METHOD -= set(SEPARATORS)

class Method(unicode):
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
        if raw not in STANDARD_METHODS: # fast for 99.999% case
            for i, byte in enumerate(raw):
                if (i == 64) or (byte not in BYTES_ALLOWED_IN_METHOD):

                    # "This is the appropriate response when the server does
                    #  not recognize the request method and is not capable of
                    #  supporting it for any resource."
                    #
                    #  http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

                    safe = ascii_dammit(raw)
                    raise Response(501, "Your request-method violates RFC "
                                        "2616: %s" % safe)

        obj = super(Method, cls).__new__(cls, raw.decode('ASCII'))
        obj.raw = raw
        return obj


# Request -> Line -> URI
# ......................

class URI(unicode):
    """Represent the Request-URI in the first line of an HTTP Request message.

    XXX spec-ify this

    """

    __slots__ = ['scheme', 'username', 'password', 'host', 'port', 'path',
                 'querystring', 'raw']

    def __new__(cls, raw):

        # split str and not unicode so we can store .raw for each subobj
        uri = urlparse.urlsplit(raw)

        # scheme is going to be ASCII 99.99999999% of the time
        scheme = UnicodeWithRaw(uri.scheme)

        # let's decode username and password as url-encoded UTF-8
        no_None = lambda o: o if o is not None else ""
        parse = lambda o: UnicodeWithRaw(urllib.unquote(no_None(o)))
        username = parse(uri.username)
        password = parse(uri.password)

        # host we will decode as IDNA, which may raise UnicodeError
        host = UnicodeWithRaw(no_None(uri.hostname), 'IDNA')

        # port is IntWithRaw (will be 0 if absent), which is fine
        port = IntWithRaw(uri.port)

        # path and querystring get bytes and do their own parsing
        path = Path(uri.path)  # further populated in gauntlet
        querystring = Querystring(uri.query)

        # we require that the uri as a whole be decodable with ASCII
        decoded = raw.decode('ASCII')
        obj = super(URI, cls).__new__(cls, decoded)
        obj.scheme = scheme
        obj.username = username
        obj.password = password
        obj.host = host
        obj.port = port
        obj.path = path
        obj.querystring = querystring
        obj.raw = raw
        return obj


# Request -> Line -> URI -> Path

class Path(Mapping):
    """Represent the path of a resource.

    This is populated by aspen.gauntlet.virtual_paths.

    """

    def __init__(self, raw):
        self.decoded = urllib.unquote(raw).decode('UTF-8')
        self.raw = raw


# Request -> Line -> URI -> Querystring

class Querystring(Mapping):
    """Represent an HTTP querystring.
    """

    def __init__(self, raw):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.decoded = urllib.unquote_plus(raw).decode('UTF-8')
        self.raw = raw
        Mapping.__init__(self, cgi.parse_qs( self.decoded
                                           , keep_blank_values = True
                                           , strict_parsing = False
                                            ))


# Request -> Line -> Version
# ..........................

versions = { 'HTTP/0.9': ((0, 9), u'HTTP/0.9')
           , 'HTTP/1.0': ((1, 0), u'HTTP/1.0')
           , 'HTTP/1.1': ((1, 1), u'HTTP/1.1')
            }  # Go ahead, find me another version.

version_re = re.compile('HTTP/\d+\.\d+')

class Version(unicode):
    """Represent the version in an HTTP status line. HTTP/1.1. Like that.

        HTTP-Version   = "HTTP" "/" 1*DIGIT "." 1*DIGIT

        (http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html)

    """

    __slots__ = ['major', 'minor', 'info', 'raw']

    def __new__(cls, raw):
        version = versions.get(raw, None)
        if version is None: # fast for 99.999999% case
            safe = ascii_dammit(raw)
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

        host = self.get('X-Forwarded-Host', self['Host']) # KeyError raises 400
        self.host = UnicodeWithRaw(host, encoding='idna')


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        scheme = 'https' if self.get('HTTPS', False) else 'http'
        self.scheme = UnicodeWithRaw(scheme)


# Request -> Body
# ---------------

class Body(Mapping):
    """Represent the body of an HTTP request.
    """

    def __init__(self, headers, fp, server_software):
        """Takes a str, a file-like object, and another str.

        If the Mapping API is used (in/one/all/has), then the iterable will be
        read and parsed as media of type application/x-www-form-urlencoded or
        multipart/form-data, according to content_type.

        """
        typecheck(headers, Headers, server_software, str)
        self.raw = self._read_raw(server_software, fp)  # XXX lazy!
        parsed = self._parse(headers, self.raw)
        if parsed is None:
            # There was no content-type. Use self.raw.
            pass
        else:
            for k in parsed.keys():
                v = parsed[k]
                if isinstance(v, cgi.MiniFieldStorage):
                    v = v.value.decode("UTF-8")  # XXX Really? Always UTF-8?
                else:
                    assert isinstance(v, cgi.FieldStorage), v
                    if v.filename is None:
                        v = v.value.decode("UTF-8")
                self[k] = v


    def _read_raw(self, server_software, fp):
        """Given str and a file-like object, return a bytestring.
        """
        if not server_software.startswith('Rocket'):  # normal
            raw = fp.read()
        else:                                                       # rocket

            # Email from Rocket guy: While HTTP stipulates that you shouldn't
            # read a socket unless you are specifically expecting data to be
            # there, WSGI allows (but doesn't require) for that
            # (http://www.python.org/dev/peps/pep-3333/#id25).  I've started
            # support for this (if you feel like reading the code, its in the
            # connection class) but this feature is not yet production ready
            # (it works but it way too slow on cPython).
            #
            # The hacky solution is to grab the socket from the stream and
            # manually set the timeout to 0 and set it back when you get your
            # data (or not).
            #
            # If you're curious, those HTTP conditions are (it's better to do
            # this anyway to avoid unnecessary and slow OS calls):
            # - You can assume that there will be content in the body if the
            #   request type is "POST" or "PUT"
            # - You can figure how much to read by the "CONTENT_LENGTH" header
            #   existence with a valid integer value
            #   - alternatively "CONTENT_TYPE" can be set with no length and
            #     you can read based on the body content ("content-encoding" =
            #     "chunked" is a good example).
            #
            # Here's the "hacky solution":

            _tmp = fp._sock.timeout
            fp._sock.settimeout(0) # equiv. to non-blocking
            try:
                raw = fp.read()
            except Exception, exc:
                if exc.errno != 35:
                    raise
                raw = ""
            fp._sock.settimeout(_tmp)

        return raw


    def _parse(self, headers, raw):
        """Takes a dict and a bytestring.

        http://www.w3.org/TR/html401/interact/forms.html#h-17.13.4

        """
        typecheck(headers, Headers, raw, str)


        # Switch on content type.

        parts = [p.strip() for p in headers.get("Content-Type", "").split(';')]
        content_type = parts.pop(0)

        # XXX Do something with charset.
        params = {}
        for part in parts:
            if '=' in part:
                key, val = part.split('=', 1)
                params[key] = val

        if content_type == "application/x-www-form-urlencoded":
            # Decode.
            pass
        elif content_type == "multipart/form-data":
            # Deal with bytes.
            pass
        else:
            # Bail.
            return None


        # Force the cgi module to parse as we want. If it doesn't find
        # something besides GET or HEAD here then it ignores the fp
        # argument and instead uses environ['QUERY_STRING'] or even
        # sys.stdin(!). We want it to parse request bodies even if the
        # method is GET (we already parsed the querystring elsewhere).

        environ = {"REQUEST_METHOD": "POST"}


        return cgi.FieldStorage( fp = cgi.StringIO(raw)  # Ack.
                               , environ = environ
                               , headers = headers
                               , keep_blank_values = True
                               , strict_parsing = True
                                )
