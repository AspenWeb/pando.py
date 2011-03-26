import urllib
import urlparse
from Cookie import CookieError, SimpleCookie

from aspen.http.headers import Headers
from aspen.http.wwwform import WwwForm


class Path(dict):
    def __init__(self, bytes):
        self.raw = bytes
        dict.__init__(self)
    def __str__(self):
        return self.raw


class Request(object):
    """Represent an HTTP Request message. Attributes:

    http://sync.in/aspen-request

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
        self.path = Path(urlparts[2]) # populated by Website
        self.raw_querystring = urlparts[4]
        self.qs = WwwForm(self.raw_querystring)
        self.url = self.rebuild_url() # needs things above
        self.urlparts = urlparse.urlparse(self.url)

        self.transport = None # set by Website for *.sock files
        self.session_id = None # set by Website for *.sock files
        self.root = '' # set by Website
        self.fs = '' # set by Website
        self.namespace = {} # populated by user in inbound hooks

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

        url += urllib.quote(self.path.raw)
        # screw params, fragment?
        if self.raw_querystring:
            url += '?' + self.raw_querystring
        return url


