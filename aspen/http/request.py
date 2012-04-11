"""Define a Request class and child classes.

Here is how we analyze the structure of an HTTP message, along with the objects
we use to model each:

    - request                   Request
        - line                  Line
            - method            Method      ASCII
            - url               URL         
                - path          Path        
                - querystring   Querystring 
            - version           Version     ASCII
        - headers               Headers     str
            - cookie            Cookie      str
            - host              unicode     str
            - scheme            unicode     str
        - body                  Body        Content-Type?

"""
import cgi
import urllib
import urlparse
from Cookie import CookieError, SimpleCookie

from aspen import Response
from aspen.http.baseheaders import BaseHeaders
from aspen.http.mapping import Mapping
from aspen.context import Context


# Line
# ====

class Line(unicode):
    """Represent the first line of an HTTP Request message.
    """

    def __new__(cls, method, url, version):
        """Takes three bytestrings.
        """
        bytes = " ".join([method, url, version])
        method = Method(method)
        url = URL(url)
        version = Version(version)
        decoded = u" ".join([method, url, version])

        obj = super(Line, cls).__new__(cls, decoded)
        obj.method = method
        obj.url = url
        obj.version = version
        obj.raw = bytes
        return obj


class Method(unicode):
    """Represent the HTTP method in the first line of an HTTP Request message.
    """

    __slots__ = ['raw']

    def __new__(cls, bytes):
        obj = super(Method, cls).__new__(cls, bytes.decode('UTF-8'))
        obj.raw = bytes
        return obj


class UnicodeWithRaw(unicode):
    """Generis subclass of unicode to store the underlying raw bytestring.
    """

    __slots__ = ['raw']

    def __new__(cls, bytes, encoding="UTF-8"):
        obj = super(UnicodeWithRaw, cls).__new__(cls, bytes.decode(encoding))
        obj.raw = bytes
        return obj


class URL(unicode):
    """Represent the URL in the first line of an HTTP Request message.
    """
   
    def __new__(cls, bytes):

        # we require that the url as a whole be decodable with ASCII
        decoded = bytes.decode('ASCII')
        obj = super(URL, cls).__new__(cls, decoded)

        # split str and not unicode so we can store .raw for each subobj
        url = urlparse.urlsplit(bytes)

        # scheme is going to be ASCII 99.99999999% of the time
        obj.scheme      = UnicodeWithRaw(url.scheme)

        # let's decode username and password as url-encoded UTF-8
        no_None = lambda o: o if o is not None else ""
        parse = lambda o: UnicodeWithRaw(urllib.unquote(no_None(o)))
        obj.username    = parse(url.username)
        obj.password    = parse(url.password)

        # host we will decode as IDNA, which may raise UnicodeError
        obj.host        = UnicodeWithRaw(no_None(url.hostname), 'IDNA')

        # port is int or None, which is fine
        obj.port        = url.port

        # path and querystring get bytes and do their own parsing
        obj.path        = Path(url.path)  # further populated in gauntlet
        obj.querystring = Querystring(url.query)

        obj.raw = bytes
        return obj


versions = { 'HTTP/0.9': ((0, 9), u'HTTP/0.9') 
           , 'HTTP/1.0': ((1, 0), u'HTTP/1.0') 
           , 'HTTP/1.1': ((1, 1), u'HTTP/1.1')
            }  # Go ahead, find me another version.

class Version(unicode):
    """Represent the version in an HTTP status line. HTTP/1.1. Like that.
    """

    __slots__ = ['major', 'minor', 'info', 'raw']

    def __new__(cls, bytes):
        version = versions.get(bytes.upper(), None)
        if version is None:
            raise Response(400, body="Bad HTTP version: %s" % bytes)
        version, decoded = version

        obj = super(Version, cls).__new__(cls, decoded)
        obj.major = version[0]  # 1
        obj.minor = version[1]  # 1
        obj.info = version      # (1, 1)
        obj.raw = bytes         # 'hTtP/1.1'
        return obj


class Path(Mapping):
    """Represent the path of a resource.

    This is populated by aspen.gauntlet.virtual_paths.

    """
   
    def __init__(self, bytes):
        self.decoded = urllib.unquote(bytes).decode('UTF-8')
        self.raw = bytes


class Querystring(Mapping):
    """Represent an HTTP querystring.
    """

    def __init__(self, bytes):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.decoded = urllib.unquote_plus(bytes).decode('UTF-8')
        self.raw = bytes
        Mapping.__init__(self, cgi.parse_qs( self.decoded
                                           , keep_blank_values = True
                                           , strict_parsing = False
                                            ))


# Headers
# =======

class Headers(BaseHeaders):
    """Model headers in an HTTP Request message.
    """

    def __init__(self, raw):
        """Extend to add extra attributes.
        """
        BaseHeaders.__init__(self, raw)
      

        # Cookie
        # ======

        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.get('Cookie', ''))
        except CookieError:
            pass


        # Host
        # ====
        # Per the spec, respond with 400 if no Host header is given. However,
        # we prefer X-Forwarded-For if that is available.
        
        self.host = self.get( 'X-Forwarded-Host'    # preferred
                            , self['Host']          # fall-back
                             ).decode('idna')


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        self.scheme = 'https' if self.get('HTTPS', False) else 'http'


# Body
# ====

class Body(Mapping):
    """Represent the body of an HTTP request.
    """

    def __init__(self, content_type, s_iter):
        """Takes an encoding type and an iterable of bytestrings.
        
        If the Mapping API is used (in/one/all/has), then the iterable will be
        read and parsed as media of type application/x-www-form-urlencoded or
        multipart/form-data, according to enctype.

        """
        self.content_type = content_type 
        self.s_iter = s_iter

    _raw = ""
    def raw(self):
        if not self._raw:
            self._raw = "".join(self.s_iter)
        return self._raw
    raw = property(raw) # lazy


    # Extend Mapping to parse.
    # ========================

    def _parse(self):
        if self.content_type.startswith('multipart/form-data'):
            return cgi.FieldStorage( fp = cgi.StringIO(self.raw)
                                   , environ = {} # XXX?
                                   , strict_parsing = True 
                                    )

    if 0: # XXX What I do wif it?
        if not environ.get('SERVER_SOFTWARE', '').startswith('Rocket'):
            # normal case
            self._body = environ['wsgi.input'].read()
        else:
            # rocket engine

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

            _tmp = environ['wsgi.input']._sock.timeout
            environ['wsgi.input']._sock.settimeout(0) # equiv. to non-blocking
            try:
                self._raw_body = environ['wsgi.input'].read()
            except Exception, exc:
                if exc.errno != 35:
                    raise
                self._raw_body = ""
            environ['wsgi.input']._sock.settimeout(_tmp)


# Request
# =======

class Request(object):
    """Represent an HTTP Request message.
    """

    socket = None
    resource = None
    original_resource = None

    def __init__(self, method='GET', url='/', version='HTTP/1.1', 
            headers='', body=None):
        """Takes four bytestrings and an iterable of bytestrings.
        """
        try:
            self.__unsafe_init__(method, url, version, headers, body) 
        except UnicodeError:
            raise Response(400, body="Error decoding request.") # XXX Where?!

    def __unsafe_init__(self, method, url, version, headers, body): 
        """Do the real initialization work. May raise UnicodeDecodeError.
        """

        # Line
        # ====

        self.line = Line(method, url, version)


        # Headers
        # =======
        # The Headers object parses out scheme, host, and cookie for us.

        if not headers:
            headers = 'Host: localhost'
        self.headers = Headers(headers)

        
        # Body
        # ====

        if body is None:
            body = ['']
        content_type = self.headers.get('Content-Type', '')
        self.body = Body(self.headers, body)

        
        # Context 
        # ============
        # This dictionary subclass will be the basis for the context for 
        # dynamic simplates.

        self.context = Context(self)
 

    def __str__(self):
        return "<%s %s>" % (self.line.method.raw, self.line.url.path.raw)
    __repr__ = __str__

    @classmethod
    def from_wsgi(cls, environ):
        """Parse instantiables from a WSGI environ.

        It would be more efficient to parse directly for the API we want, but
        then we lose the benefits of playing the WSGI game. People love their
        gunicorn.

        """
        
        # Line
        # ====

        method = environ['REQUEST_METHOD']
        url = environ['PATH_INFO']
        qs = environ.get('QUERY_STRING', '')
        if qs:
            url += '?' + qs
        version = environ['SERVER_PROTOCOL']


        # Headers
        # =======

        # For some reason there are a couple keys that CherryPyWSGIServer 
        # explicitly doesn't include as HTTP_ keys.
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
        headers = '\r\n'.join(headers) # *sigh*

        
        # Body
        # ====
        
        body = environ['wsgi.input']
        
        return cls(method, url, version, headers, body)


    # Public Methods
    # ==============

    _raw = ""
    def raw(self):
        if not self._raw:
            fmt = "%s\r\n%s\r\n\r\n%s" 
            self._raw = fmt % (self.line.raw, self.headers.raw, self.body.raw)
        return self._raw
    raw = property(raw)

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

    def redirect(self, location, code=None, permanent=False):
        """Given a string, an int, and a boolean, raise a Response.

        If code is None then it will be set to 301 (Moved Permanently) if
        permanent is True and 302 (Found) if it is False.

        XXX Some day port this:

            http://cherrypy.org/browser/trunk/cherrypy/_cperror.py#L154

        """
        if code is None:
            code = permanent is True and 301 or 302
        raise Response(code, headers={'Location': location})
