import os
import cgi
import urllib
import urlparse
from Cookie import CookieError, SimpleCookie

from diesel.protocols.http import ( http_response as DieselResponse
                                  , HttpHeaders as DieselHeaders
                                  , status_strings
                                   )


class Mapping(object):
    """Base class for HTTP mappings.

    HTTP forms and headers may have a single item or a list of items as the
    value. So while Python dictionary semantics work for almost everything, it
    is better (IMO) for the API to force you to be explicit about whether you
    are expecting a single item or list of items. We do that here by providing
    'one' and 'all' methods, rather than item access and a 'get' method.
    Furthermore, this class supports iteration over keys, but not iteration
    over values. Iterate over keys, and then use one or all.

    All API here operates on a self._dict dictionary. Set that in subclass
    constructors.

    """

    def __init__(self, **kw):
        self._dict = {}
        for name, value in kw.iteritems():
            self.set(name, value)

    def add(self, name, value):
        """Given a name and value, add another entry.
        """
        if name not in self._dict:
            self._dict[name] = value
        self._dict[name].append(value)

    def __contains__(self, name):
        return name.lower() in self._dict

    def all(self, name, default=None):
        """Given a name, return a list of values.
        """
        if default is None:
            default = []
        return self._dict.get(name, default)
       
    def one(self, name, default=None):
        return self._dict.get(name.lower(), [default])[0]

    def __iter__(self):
        return self._dict

    def __in__(self, name):
        """Given a name, return True if it is known in the mapping.
        """
        return name in self._dict

    def __iter__(self):
        return self._dict.__iter__()

    def keys(self):
        """Return a list of names.
        """
        return self._dict.keys()

    def set(self, name, value):
        """Given a name and value, set the value, clearing all others.
        
        Pass None to remove.

        """
        if value is None:
            del self._dict[name]
        self._dict[name.lower()] = [str(value).strip()] # TODO unicode?


    # Convenience methods for coercing to bool.
    # =========================================

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
        if name not in self._dict:
            return default 
        value = self._dict[name].lower()
        if value not in YES_NO:
            raise ConfigurationError( "%s should be 'yes' or 'no', not %s" 
                                    % (name, self._dict[name])
                                     )
        return value in YES 

class Headers(Mapping):
    """Represent the headers in an HTTP Request message.
    """

    def __init__(self, headers):
        """Takes headers as a string.
        """
        diesel_headers = DieselHeaders()
        diesel_headers.parse(headers)
        self._diesel_headers = diesel_headers
        Mapping.__init__(self, **diesel_headers._headers)

    def to_http(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self._dict.iteritems():
            for value in values:
                out.append('%s: %s' % (header.title(), value))
        return '\r\n'.join(out)

class WwwForm(Mapping):
    """Represent a WWW form.
    """

    def __init__(self, s):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self._dict = cgi.parse_qs( s
                                 , keep_blank_values = True
                                 , strict_parsing = False
                                  )


class Request(object):
    """Represent an HTTP Request message. Attributes:

    request.url = urlparse.urlparse()
    request.url.base = "http://localhost"
    request.url.full = "http://localhost/foo/bar.html?baz=1"
    request.url.path = {"foo": "foo", "bar": "bar", 0: "foo", 1: "bar"}
    request.url.path.raw = "/foo/bar.html"
    request.url.qs = WwwForm()
    request.url.qs.raw = "baz=1"
    request.url.raw = "/foo/bar.html?baz=1"
    request.url.scheme = ? # SSL header? conf? port?

    request.method = "POST"
    request.version = (1, 1)
    request.version.raw = "HTTP/1.1"

    request.headers = Headers()
    request.headers.host = "localhost" # harmonized from Host, X-Host, conf
    request.headers.cookie = Cookie()
    request.headers.cookie.raw = "Set-Cookie: blah\r\nSet-Cookie: blah\r\n"
    request.headers.raw = "X-Foo: Bar\r\nAccept: gzip\r\n\r\n"

    request.body = WwwForm()
    request.body.raw = ""

    """
   
    def hydrate(self):
        """Populate a number of attributes on self based on primitives.
        """
        self.body = WwwForm(self.raw_body)
        self.headers = Headers(self.raw_headers)
        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.headers.one('Cookie', ''))
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
        self.raw_headers = request.headers and request.headers.format() or ''
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
        scheme = self.headers.one('HTTPS') and 'https' or 'http'
        url = scheme
        url += '://'

        if 'X-Forwarded-Host' in self.headers:
            url += self.headers.one('X-Forwarded-Host')
        elif 'Host' in self.headers:
            url += self.headers.one('Host')
        else:
            # per spec, return 400 if no Host header given
            raise Response(400)

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
            self.cookie.load(self.headers.one('Cookie', ''))
        except CookieError:
            pass


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status())

    def _status(self):
        return status_strings.get(self.code, ('???','Unknown HTTP status'))

    def _to_diesel(self, _diesel_request):
        """This actually sends bits over the wire(!).
        """
        for morsel in self.cookie.values():
            self.headers.add('Set-Cookie', morsel.OutputString())
        self.headers._diesel_headers._headers = self.headers._dict
        return DieselResponse( _diesel_request
                             , self.code
                             , self.headers._diesel_headers
                             , self.body
                              )

    def _to_http(self, version):
        status_line = "HTTP/%s" % version
        headers = self.headers.to_http()
        body = self.body
        if self.headers.one('Content-Type', '').startswith('text/'):
            body = body.replace('\n', '\r\n')
            body = body.replace('\r\r', '\r')
        return '\r\n'.join([status_line, headers, '', body])
