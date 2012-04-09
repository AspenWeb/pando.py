"""Define a Request class and child classes.

Here is how we analyze the structure of an HTTP message, along with the objects
we use to model each:

    - request                   Request
        - line                  Line
            - method            Method
            - url               URL
                - path          Path
                - querystring   Querystring
            - version           Version
        - headers               Headers
            - cookie            Cookie
            - host              unicode
            - scheme            unicode
        - body                  Body

"""
import cgi
import urlparse
from Cookie import CookieError, SimpleCookie

from aspen import Response
from aspen.http.baseheaders import BaseHeaders
from aspen.http.mapping import Mapping
from aspen.context import Context


# Line
# ====

class Line(unicode):

    __slots__ = ['method', 'url', 'version', 'raw']

    def __new__(cls, method, url, version):
        """Takes three bytestrings.
        """
        raw = " ".join([method, url, version])
        method = Method(method)
        url = URL(url)
        version = Version(version)
        line = u" ".join([method, url, version.decoded])
        obj = super(Line, cls).__new__(cls, line)
        obj.method = method
        obj.url = url
        obj.version = version
        obj.raw = raw
        return obj
    
    def __repr__(self):
        return u"<Line(unicode): %s>" % self


class Method(unicode):

    __slots__ = ['raw']

    def __new__(cls, bytes):
        try:
            method = bytes.decode('ASCII').upper()
        except UnicodeDecodeError:
            raise Response(400)
        obj = super(Method, cls).__new__(cls, method)
        obj.raw = bytes
        return obj
    
    def __repr__(self):
        return u"<Method(unicode): %s>" % self


class URL(unicode):
   
    __slots__ = ['raw', 'parsed', 'path', 'querystring']

    def __new__(cls, bytes):
        url = bytes.decode('utf-8') # XXX really?
        obj = super(URL, cls).__new__(cls, url)
        parsed = urlparse.urlparse(url)
        obj.path = Path(parsed[2]) # further populated by Website
        obj.querystring = Querystring(parsed[4])
        obj.raw = bytes
        return obj

    def __repr__(self):
        return u"<URL(unicode): %s>" % self


class Path(dict):
    # Populated by aspen.website.Website.
   
    __slots__ = ['raw', 'decoded']

    def __init__(self, bytes):
        self.raw = bytes
        self.decoded = bytes.decode('utf-8') # XXX really?

    def __repr__(self):
        return u"<Path(dict): %s>" % self.keys()


class Querystring(Mapping):
    """Represent an HTTP querystring.
    """

    def __init__(self, s):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.raw = s
        self._dict = cgi.parse_qs( s
                                 , keep_blank_values = True
                                 , strict_parsing = False
                                  )


class Version(tuple):
    """Represent the version in an HTTP status line. HTTP/1.1. Like that.
    """

    def __new__(cls, bytes):
        http, version = bytes.split('/')    # ("HTTP", "1.1")
        parts = version.split('.')          # (1, 1)
        try:
            major, minor = int(parts[0]), int(parts[1])
        except ValueError:                  # (1, 2, 3) or ('foo', 'bar')
            raise Response(400)

        obj = super(Version, cls).__new__(cls, (major, minor))
        obj.major = major                   # 1
        obj.minor = minor                   # 1
        obj.raw = bytes                     # HTTP/1.1
        obj.decoded = bytes.decode('utf-8') # warty?
        return obj

    def __repr__(self):
        return u"<Version(tuple): %s>" % self


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
            self.cookie.load(self.one('Cookie', ''))
        except CookieError:
            pass


        # Host
        # ====
        # Per the spec, respond with 400 if no Host header is given. However,
        # we prefer X-Forwarded-For if that is available.
        
        if 'Host' not in self:
            raise Response(400)
        self.host = self.one( 'X-Forwarded-Host'    # preferred
                            , self.one('Host')      # fall-back
                             ).decode('idna')


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        self.scheme = self.one('HTTPS', False) and u'https' or u'http'


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

    def __contains__(self, name):
        self._parse()
        return super(Body, self).__contains__(name);

    def all(self, name, default=None):
        self._parse()
        return super(Body, self).all(name, default);

    def one(self, name, default=None):
        self._parse()
        return super(Body, self).one(name, default);

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
        content_type = self.headers.one('Content-Type', '')
        self.body = Body(content_type, body)

        
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
        val = self.headers.one('X-Requested-With', '')
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
