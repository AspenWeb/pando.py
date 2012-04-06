from collections import defaultdict
from Cookie import CookieError, SimpleCookie

from aspen.http.mapping import Mapping


class Headers(Mapping):
    """Represent the headers in an HTTP Request or Response message.
    """

    def __init__(self, headers):
        """Takes headers as a string.
        """
        self.raw = headers
        Mapping.__init__(self)
        hd = defaultdict(list)
        for line in headers.splitlines():
            k, v = line.strip().split(':', 1)
            hd[k.strip().lower()].append(v.strip())
        self._dict.update(hd)

    def to_http(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self._dict.iteritems():
            for value in values:
                out.append('%s: %s' % (header.title(), value))
        return '\r\n'.join(out)


    # Extend Mapping to make case-insensitive.
    # ========================================

    def __contains__(self, name):
        return name.lower() in self._dict

    def __in__(self, name):
        return super(Headers, self).__in__(name.lower());

    def all(self, name, default=None):
        return super(Headers, self).all(name.lower(), default);

    def one(self, name, default=None):
        return super(Headers, self).one(name.lower(), default);

    def set(self, name, value):
        return super(Headers, self).set(name.lower(), value);


class RequestHeaders(Headers):
    """Model headers in an HTTP Request message.
    """

    def __init__(self, headers):
        """Extend to add extra attributes.
        """
        super(RequestHeaders, self).__init__(headers)
      

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
            from aspen import Response # dodge circular import
            raise self.Response(400)
        self.host = self.one( 'X-Forwarded-Host'    # preferred
                            , self.one('Host')      # fall-back
                             ).decode('idna')


        # Scheme
        # ======
        # http://docs.python.org/library/wsgiref.html#wsgiref.util.guess_scheme

        self.scheme = self.one('HTTPS', False) and u'https' or u'http'


ResponseHeaders = Headers
