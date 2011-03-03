import os
import cgi
import urllib
import urlparse
from Cookie import CookieError, SimpleCookie

from diesel.protocols.http import ( http_response as DieselResponse
                                  , HttpHeaders as DieselHeaders
                                  , status_strings
                                   )


class Headers(object):
    """Represent the headers in an HTTP Request message.
    """

    def __init__(self, headers):
        """Takes headers as a string.
        """
        diesel_headers = DieselHeaders()
        diesel_headers.parse(headers)
        self._headers = diesel_headers 

    def all(self, name, default=None):
        """Given a header name, return a list of values.
        """
        if default is None:
            default = []
        return self._headers.get(name, default)
       
    def get(self, name, default=None):
        """Given a header name, return the first known value.
        """
        return self._headers.get_one(name, default)

    def has(self, name):
        """Given a header name, return True if it is known in the form.
        """
        return name in self._headers

    def add(self, name, value):
        """Given a header name and value, add another header entry.
        """
        if name not in self._headers:
            # work around https://github.com/jamwt/diesel/issues#issue/6
            self._headers.set(name, value)
        self._headers.add(name, value)

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
       
    def get(self, name, default=None):
        """Given a field name, return the first known value.
        """
        if name in self._form:
            return self._form[name][0]
        return default

    def has(self, name):
        """Given a field name, return True if it is known in the form.
        """
        return name in self._form

    def yes(self, name):
        """Given a key name, return a boolean.
        
        The value for the key must be in the set {0,1,yes,no,true,false},
        case-insensistive. If the key is not in this section, we return True.

        """
        return self._yes_no(name, True)

    def no(self, name):
        """Given a key name, return a boolean.
        
        The value for the key must be in the set {0,1,yes,no,true,false},
        case-insensistive. If the key is not in this section, we return False.

        """
        return self._yes_no(name, False)

    def _yes_no(self, name, default):
        if name not in self._form:
            return default 
        val = self._form[name].lower()
        if val not in YES_NO:
            raise ConfigurationError( "%s should be 'yes' or 'no', not %s" 
                                    % (name, self._form[name])
                                     )
        return val in YES 



class Request(object):
    """Represent an HTTP Request message. Attributes:

        body            WwwForm object
        cookie          a Cookie.SimpleCookie object
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
   
    def hydrate(self):
        """Populate a number of attributes on self based on primitives.
        """
        self.body = WwwForm(self.raw_body)
        self.headers = Headers(self.raw_headers)
        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.headers.get('Cookie', ''))
        except CookieError:
            pass

        urlparts = urlparse.urlparse(self.raw_url)
        self.path = urlparts[2]
        self.raw_querystring = urlparts[4]
        self.qs = WwwForm(self.raw_querystring)
        self.url = self.rebuild_url() # needs things above
        self.urlparts = urlparse.urlparse(self.url)

        self.transport = None # set by Website for *.sock files
        self.session_id = None # set by Website for *.sock files
        self.root = '' # set by Website
        self.fs = '' # set by Website

    @classmethod
    def from_diesel(cls, request):
        """Set primitives from a diesel request.
        """
        self = cls()
        self._diesel_request = request
        self.method = request.method
        self.version = request.version
        self.raw_headers = request.headers.format()
        self.raw_body = request.body and request.body or ''
        self.remote_addr = request.remote_addr and request.remote_addr or ''
        self.raw_url = request.url

        self.hydrate()
        return self

    def __str__(self):
        return "<%s %s>" % (self.method, self.path)
    __repr__ = __str__


    def rebuild_url(self):
        """Return a full URL for this request, per PEP 333:

            http://www.python.org/dev/peps/pep-0333/#url-reconstruction

        This function is kind of naive.

        """
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme
        scheme = self.headers.get('HTTPS') and 'https' or 'http'
        url = scheme
        url += '://'

        if self.headers.has('X-Forwarded-Host'):
            url += self.headers.get('X-Forwarded-Host')
        elif self.headers.has('Host'):
            url += self.headers.get('Host')
        else:
            raise Response(500) # naive :-/

        url += urllib.quote(self.path)
        # screw params, fragment?
        if self.raw_querystring:
            url += '?' + self.raw_querystring
        return url

class Response(Exception):
    """Represent an HTTP Response message.
    """

    def __init__(self, code=200, body='', headers=None):
        """Takes an int, a string, and a dict (or list of tuples).

            - code      an HTTP response code, e.g., 404
            - body      the message body as a string
            - headers   a Headers instance
            - cookie    a Cookie.SimpleCookie instance

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
        self.headers = Headers('')
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers.add(k, v)
        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.headers.get('Cookie', ''))
        except CookieError:
            pass


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status())

    def _status(self):
        return status_strings.get(self.code, ('???','Unknown HTTP status'))

    def _to_diesel(self, _diesel_request):
        for morsel in self.cookie.values():
            self.headers.add('Set-Cookie', morsel.OutputString())
        return DieselResponse( _diesel_request
                             , self.code
                             , self.headers._headers
                             , self.body
                              )

    def _to_http(self, version):
        status_line = "HTTP/%s %s" % (self, version)
        headers = self.headers.to_http()
        body = self.body
        if self.headers.get('Content-Type', '').startswith('text/'):
            body = body.replace('\n', '\r\n')
            body = body.replace('\r\r', '\r')
        return '\r\n'.join([status_line, headers, '', body])
