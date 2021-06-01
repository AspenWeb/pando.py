"""
:mod:`response`
---------------
"""

import os
import sys

from . import status_strings
from .baseheaders import BaseHeaders as Headers


class CloseWrapper:
    """Conform to WSGI's facility for running code *after* a response is sent.
    """

    def __init__(self, request, body):
        self.request = request
        self.body = body

    def __iter__(self):
        return iter(self.body)

    def close(self):
        # No longer using this since we ripped out Socket.IO support.
        pass


class Response(Exception):
    """Represent an HTTP Response message.
    """

    request = None
    whence_raised = (None, None)

    def __init__(self, code=200, body='', headers=None):
        """Takes an int, a string, a dict.

            - code      an HTTP response code, e.g., 404
            - body      the message body as a string
            - headers   a dict, list, or bytestring of HTTP headers

        Code is first because when you're raising your own Responses, they're
        usually error conditions. Body is second because one more often wants
        to specify a body without headers, than a header without a body.

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif not isinstance(body, (bytes, str)) and not hasattr(body, '__iter__'):
            raise TypeError("'body' must be a string or iterable of strings")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")

        Exception.__init__(self)
        self.code = code
        self.body = body
        self.headers = Headers(headers)

    def to_wsgi(self, environ, start_response, charset):
        wsgi_status = str(self._status_text())
        for morsel in self.headers.cookie.values():
            self.headers.add(b'Set-Cookie', morsel.OutputString().encode('ascii'))

        # To comply with PEP 3333 headers should be `str` (bytes in py2 and unicode in py3)
        wsgi_headers = []
        for k, vals in self.headers.items():
            try:        # XXX This is a hack. It's red hot, baby.
                k = k.encode('US-ASCII') if not isinstance(k, bytes) else k
            except UnicodeEncodeError:
                raise ValueError("Header key %s isn't US-ASCII." % k)
            for v in vals:
                try:    # XXX This also is a hack. It is also red hot, baby.
                    v = v.encode('US-ASCII') if not isinstance(v, bytes) else v
                except UnicodeEncodeError:
                    raise ValueError("Header value %s isn't US-ASCII." % k)
                if str is bytes:  # python2 shortcut, no need to decode
                    wsgi_headers.append((k, v))
                    continue
                try:
                    wsgi_headers.append((k.decode('ascii'), v.decode('ascii')))
                except UnicodeDecodeError:
                    k = k.decode('ascii', 'backslashreplace')
                    v = v.decode('ascii', 'backslashreplace')
                    raise ValueError("Header `%s: %s` isn't US-ASCII." % (k, v))

        start_response(wsgi_status, wsgi_headers)
        body = self.body
        if not isinstance(body, (list, tuple)):
            body = [body]
        body = (x.encode(charset) if not isinstance(x, bytes) else x for x in body)
        return CloseWrapper(self.request, body)

    def __repr__(self):
        return "<Response: %s>" % self._status_text()

    def __str__(self):
        body = self.body
        if len(body) < 500:
            if not isinstance(body, str):
                if isinstance(body, bytes):
                    body = body.decode('ascii', 'backslashreplace')
                else:
                    body = str(body)
            return ': '.join((self._status_text(), body))
        return self._status_text()

    def _status_text(self):
        return "%d %s" % (self.code, self._status())

    def _status(self):
        return status_strings.get(self.code, 'Unknown HTTP status')

    def _to_http(self, version):
        """Given a version string like 1.1, return an HTTP message (bytestring).
        """
        status_line = ("HTTP/%s" % version).encode('ascii')
        headers = self.headers.raw
        body = self.body
        if self.headers.get(b'Content-Type', b'').startswith(b'text/'):
            body = body.replace(b'\n', b'\r\n')
            body = body.replace(b'\r\r', b'\r')
        return b'\r\n'.join([status_line, headers, b'', body])

    def set_whence_raised(self):
        """Sets self.whence_raised

        It's a tuple, (filename, linenum) where we were raised from.

        This function needs to be called from inside the `except` block.

        """
        filepath = linenum = None
        cls, response, tb = sys.exc_info()
        if response is self:
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame

            # filepath
            filepath = tb.tb_frame.f_code.co_filename
            # Try to return the path relative to project_root
            if self.request and getattr(self.request, 'website'):
                filepath = os.path.relpath(filepath, self.request.website.project_root)
            else:
                # Fall back to returning only the last two segments
                filepath = os.sep.join(filepath.split(os.sep)[-2:])

            # linenum
            linenum = frame.f_lineno
        self.whence_raised = (filepath, linenum)
