"""Define a Request class.
"""
import cgi

from aspen import Response
from aspen.http.body import Body
from aspen.http.headers import RequestHeaders
from aspen.http.line import Line


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
METHODS = [ 'OPTIONS'
          , 'GET'
          , 'HEAD'
          , 'POST'
          , 'PUT'
          , 'DELETE'
          , 'TRACE'
          , 'CONNECT'
           ]


class Request(object):
    """Represent an HTTP Request message.

    Here is how we analyze the structure of an HTTP message, along with the
    objects we use to model each:

        - line                  Line
            - method            Method
            - url               URL
                - path          Path
                - querystring   Querystring
            - version           Version
        - headers               RequestHeaders
            - cookie            Cookie
            - host              unicode
            - scheme            unicode
        - body                  Body

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
        # The RequestHeaders object parses out scheme, host, and cookie for us.

        if not headers:
            headers = 'Host: localhost'
        self.headers = RequestHeaders(headers)

        
        # Body
        # ====

        if body is None:
            body = ['']
        content_type = self.headers.one('Content-Type', '')
        self.body = Body(content_type, body)

        
        # Other Things
        # ============
        # This namespace dictionary will be the basis for the context for
        # dynamic simplates.

        self.namespace = {}
        self.namespace['body'] = self.body
        self.namespace['headers'] = self.headers
        self.namespace['cookie'] = self.line.url.querystring
        self.namespace['path'] = self.line.url.path
        self.namespace['qs'] = self.line.url.querystring
        self.namespace['request'] = self

        for method in METHODS:
            self.namespace[method] = method == self.line.method
 

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
       
    def is_xhr(self):
        val = self.headers.one('X-Requested-With', '')
        return val.lower() == 'xmlhttprequest'
    is_xhr = property(is_xhr)

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

    def allow(self, *methods):
        """Given method strings, raise 405 if ours is not among them.

        The method names are case insensitive (they are uppercased). If 405
        is raised then the Allow header is set to the methods given.

        """
        methods = [x.upper() for x in methods]
        if self.line.method not in methods:
            raise Response(405, headers={'Allow': ', '.join(methods)})
