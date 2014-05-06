"""
aspen.http.response
~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import os
import re
import sys

from aspen.utils import ascii_dammit
from aspen.http import status_strings
from aspen.http.baseheaders import BaseHeaders as Headers


class CloseWrapper(object):
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


# Define a charset name filter.
# =============================
# "The character set names may be up to 40 characters taken from the
#  printable characters of US-ASCII."
#  (http://www.iana.org/assignments/character-sets)
#
# We're going to be slightly more restrictive. Instead of allowing all
# printable characters, which include whitespace and newlines, we're going to
# only allow punctuation that is actually in use in the current IANA list.

charset_re = re.compile("^[A-Za-z0-9:_()+.-]{1,40}$")


class Response(Exception):
    """Represent an HTTP Response message.
    """

    request = None

    def __init__(self, code=200, body='', headers=None, charset="UTF-8"):
        """Takes an int, a string, a dict, and a basestring.

            - code      an HTTP response code, e.g., 404
            - body      the message body as a string
            - headers   a Headers instance
            - charset   string that will be set in the Content-Type in the future at some point but not now

        Code is first because when you're raising your own Responses, they're
        usually error conditions. Body is second because one more often wants
        to specify a body without headers, than a header without a body.

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif not isinstance(body, basestring) and not hasattr(body, '__iter__'):
            raise TypeError("'body' must be a string or iterable of strings")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")
        elif charset_re.match(charset) is None:
            raise TypeError("'charset' must match " + charset_re.pattern)

        Exception.__init__(self)
        self.code = code
        self.body = body
        self.headers = Headers(b'')
        self.charset = charset
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers[k] = v
        self.headers.cookie.load(self.headers.get('Cookie', b''))

    def __call__(self, environ, start_response):
        wsgi_status = str(self)
        for morsel in self.headers.cookie.values():
            self.headers.add('Set-Cookie', morsel.OutputString())
        wsgi_headers = []
        for k, vals in self.headers.iteritems():
            try:        # XXX This is a hack. It's red hot, baby.
                k = k.encode('US-ASCII')
            except UnicodeEncodeError:
                k = ascii_dammit(k)
                raise ValueError("Header key %s must be US-ASCII.")
            for v in vals:
                try:    # XXX This also is a hack. It is also red hot, baby.
                    v = v.encode('US-ASCII')
                except UnicodeEncodeError:
                    v = ascii_dammit(v)
                    raise ValueError("Header value %s must be US-ASCII.")
                wsgi_headers.append((k, v))

        start_response(wsgi_status, wsgi_headers)
        body = self.body
        if isinstance(body, basestring):
            body = [body]
        body = (x.encode(self.charset) if isinstance(x, unicode) else x for x in body)
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
        headers = self.headers.raw
        body = self.body
        if self.headers.get('Content-Type', '').startswith('text/'):
            body = body.replace('\n', '\r\n')
            body = body.replace('\r\r', '\r')
        return '\r\n'.join([status_line, headers, '', body])

    def whence_raised(self):
        """Return a tuple, (filename, linenum) where we were raised from.

        If we're not the exception currently being handled then the return
        value is (None, None).

        """
        tb = filepath = linenum = None
        try:
            cls, response, tb = sys.exc_info()
            if response is self:
                while tb.tb_next is not None:
                    tb = tb.tb_next
                frame = tb.tb_frame

                # filepath
                pathparts = tb.tb_frame.f_code.co_filename.split(os.sep)[-2:]
                # XXX It'd be nice to use www_root and project_root here, but
                # self.request is None at this point afaict, and it's enough to
                # show the last two parts just to differentiate index.html or
                # __init__.py.
                filepath = os.sep.join(pathparts)

                # linenum
                linenum = frame.f_lineno
        finally:
            del tb  # http://docs.python.org/2/library/sys.html#sys.exc_info
        return filepath, linenum
