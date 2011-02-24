import os
import cgi
import urlparse
from Cookie import CookieError, SimpleCookie

from diesel.protocols.http import ( http_response as DieselResponse
                                  , HttpHeaders
                                  , status_strings
                                   )


class Headers(object):
    """Represent the headers in an HTTP Request message.
    """

    def __init__(self, diesel_headers):
        """Takes a diesel HttpHeaders object.
        """
        self._headers = diesel_headers 

    def all(self, name, default=None):
        """Given a header name, return a list of values.
        """
        if default is None:
            default = []
        return self._headers.get(name, default)
       
    def has(self, name):
        """Given a header name, return True if it is known in the form.
        """
        return name in self._headers

    def one(self, name, default=None):
        """Given a header name, return the first known value.
        """
        return self._headers.get_one(name, default)

    def set(self, name, value):
        """Given a header name and value, set the header. Pass None to remove.
        """
        if value is None:
            self._headers.remove(name)
        else:
            self._headers.set(name, value)

    def to_http(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        return self._headers.format()


class WwwForm(object):
    """Represent a WWW form.
    """

    def __init__(self, s):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self._form = cgi.parse_qs( s
                                 , keep_blank_values = True
                                 , strict_parsing = False
                                  )

    def all(self, name, default=None):
        """Given a field name, return a list of values.
        """
        if default is None:
            default = []
        return self._form.get(name, default)
       
    def has(self, name):
        """Given a field name, return True if it is known in the form.
        """
        return name in self._form

    def one(self, name, default=None):
        """Given a field name, return the first known value.
        """
        if name in self._form:
            return self._form[name][0]
        return default


class Request(object):
    """Represent an HTTP Request message. Attributes:

        body            WwwForm object
        cookie          a Cookie.SimpleCookie object
        diesel_request  the original diesel HttpRequest object
        headers         Headers object
        method          string
        path            string
        qs              WwwForm object
        remote_addr     string 
        transport       Socket.IO transport as string, or None
        url             string
        urlparts        urlparse.urlparse output
        version         HTTP version as string

    """
    
    def __init__(self, req):
        """Takes a diesel request.
        """
        self.diesel_request = req
        self.method = req.method
        self.url = req.url
        self.version = req.version
        self.headers = Headers(req.headers)
        self.body = WwwForm(req.body and req.body or '')
        self.remote_addr = req.remote_addr
        
        if self.body is None:
            self.body = ""
        if self.remote_addr is None:
            self.remote_addr = ""

        self.urlparts = urlparse.urlparse(req.url)
        self.path = self.urlparts[2]
        self.qs = WwwForm(self.urlparts[4])
        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.headers.one('Cookie'))
        except CookieError:
            pass

        self.transport = None # set by Website for *.sock files
        self.session_id = None # set by Website for *.sock files
        self.root = '' # set by Website
        self.fs = '' # set by Website


class Response(Exception):
    """Represent an HTTP Response message.
    """

    def __init__(self, code=200, body='', headers=None):
        """Takes an int, a string, and a dict (or list of tuples).

            - code        an HTTP response code, e.g., 404
            - body        the message body as a string
            - headers     a diesel.HttpHeaders instance

        Code is first because when you're raising your own Responses, they're
        usually error conditions. Body is second because one more often wants
        to specify a body without headers, than a header without a body.

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif not isinstance(body, basestring):
            raise TypeError("'body' must be a string")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")

        Exception.__init__(self)
        self.code = code
        self.body = body
        self.headers = HttpHeaders()
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers.add(k, v)


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status())

    def _status(self):
        return status_strings.get(self.code, ('???','Unknown HTTP status'))

    def to_diesel(self, diesel_request):
        for morsel in self.cookie.values():
            self.headers.add('Set-Cookie', morsel.OutputString())
        return DieselResponse( diesel_request
                             , self.code
                             , self.headers
                             , self.body
                              )

    def to_http(self, version):
        status_line = "HTTP/%s %s" % (self, version)
        headers = self.headers.to_http()
        body = self.body
        if self.headers.one('Content-Type', '').startswith('text/'):
            body = body.replace('\n', '\r\n')
            body = body.replace('\r\r', '\r')
        return '\r\n'.join([status_line, headers, '', body])
