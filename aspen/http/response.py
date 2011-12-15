from Cookie import CookieError, SimpleCookie

from aspen.http import status_strings
from aspen.http.headers import Headers


class CloseWrapper(object):
    """Conform to WSGI's facility for running code *after* a response is sent.
    """
    def __init__(self, request, body):
        self.request = request
        self.body = body
    def __iter__(self):
        return iter(self.body)
    def close(self):
        socket = getattr(self.request, "socket", None)
        if socket is not None:
            pass
            # implement some socket closing logic here
            #self.request.socket.close()


class Response(Exception):
    """Represent an HTTP Response message.
    """

    request = None

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
        elif not isinstance(body, str) and not hasattr(body, '__iter__'):
            raise TypeError("'body' must be a bytestring or iterable of "
                            "bytestrings")
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

    def __call__(self, environ, start_response):
        wsgi_status = str(self)
        for morsel in self.cookie.values():
            self.headers.add('Set-Cookie', morsel.OutputString())
        wsgi_headers = []
        for k, vals in self.headers._dict.items():
            for v in vals:
                wsgi_headers.append((k, v))
        start_response(wsgi_status, wsgi_headers)
        body = self.body
        if isinstance(body, basestring):
            body = [body]
        return CloseWrapper(self.request, body)

    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status())

    def _status(self):
        return status_strings.get(self.code, 'Unknown HTTP status')

    def _to_http(self, version):
        """Given a version string like 1.1, return an HTTP message, a string.
        """
        status_line = "HTTP/%s" % version
        headers = self.headers.to_http()
        body = self.body
        if self.headers.one('Content-Type', '').startswith('text/'):
            body = body.replace('\n', '\r\n')
            body = body.replace('\r\r', '\r')
        return '\r\n'.join([status_line, headers, '', body])

