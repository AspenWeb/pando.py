"""
:mod:`response`
---------------
"""

import os
import sys

from aspen.request_processor.dispatcher import DispatchResult, DispatchStatus
import aspen.simplates.json_ as json
from aspen.utils import Constant

from ..utils import encode_url
from . import status_strings


MISSING = Constant('MISSING')


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
            - headers   a dict or list of HTTP headers

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
        from .baseheaders import BaseHeaders as Headers
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

    def erase_cookie(self, *a, **kw):
        """Calls :meth:`pando.website.Website.erase_cookie`.
        """
        return self.website.erase_cookie(self.headers.cookie, *a, **kw)

    def error(self, code, msg=''):
        """Set :attr:`self.code` and :attr:`self.body`, then return :obj:`self`.

        Example:

        >>> raise Response().error(403, "You're not allowed to do this.")
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 403 Forbidden: You're not allowed to do this.

        """
        self.code = code
        self.body = msg
        return self

    def invalid_input(
        self, input_value, input_name, input_location, code=400,
        msg="`%s` value %s in request %s is invalid or unsupported",
    ):
        """Set :attr:`self.code` and :attr:`self.body`, then return :obj:`self`.

        Examples:

        >>> raise Response().invalid_input('XX', 'country', 'body')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `country` value 'XX' in request body is invalid or unsupported
        >>> Response().invalid_input('X' * 500, 'currency', 'querystring').body
        "`currency` value 'XXXXXXXXXXXXXXXXXXXXXXX[…]XXXXXXXXXXXXXXXXXXXXXXX' in request querystring is invalid or unsupported"

        """
        self.code = code
        input_value = repr(input_value)
        if len(input_value) > 50:
            input_value = input_value[:24] + '[…]' + input_value[-24:]
        self.body = msg % (input_name, input_value, input_location)
        return self

    def json(self, obj=MISSING, code=200):
        """Load or dump an object from or into a response body.

        >>> r = Response()
        >>> print(r.json({'foo': 'bar'}).body)
        {
            "foo": "bar"
        }
        >>> r.json()
        {'foo': 'bar'}

        """
        if obj is MISSING:
            return json.loads(self.body)
        else:
            self.code = code
            self.body = json.dumps(obj)
            self.headers[b'Content-Type'] = b'application/json'
            return self

    def redirect(self, url, code=302, trusted_url=False):
        """
        Returns the response after modifying its code, setting its ``Location`` header,
        and sanitizing the URL (unless :obj:`trusted_url` is set to :obj:`True`).
        """
        if not trusted_url:
            url = self.request.sanitize_untrusted_url(url)
        self.code = code
        self.headers[b'Location'] = encode_url(url)
        return self

    def render(self, fspath, state, **extra):
        """Render the resource file `fspath` with `state` plus `extra` as context.

        This method is an “internal redirect”, it uses a different file to generate
        the response without changing the URL on the client side. It should be
        used sparingly.

        """
        from ..state_chain import render_response
        state.update(extra)
        if 'dispatch_result' not in state:
            # `render_response` needs `state['dispatch_result']`
            state['dispatch_result'] = DispatchResult(
                DispatchStatus.okay, fspath, None, None, None
            )
        website = state['website']
        resource = website.request_processor.resources.get(fspath)
        render_response(state, resource, self, website)
        return self

    def set_cookie(self, *a, **kw):
        """Calls :meth:`pando.website.Website.set_cookie`.
        """
        return self.website.set_cookie(self.headers.cookie, *a, **kw)

    def set_whence_raised(self):
        """Sets and returns the value of `self.whence_raised`.

        It's a tuple, (filename, linenum) where we were raised from.

        This function needs to be called from inside the `except` block.

        """
        cls, exception, tb = sys.exc_info()
        if exception is self:
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            filepath = frame.f_code.co_filename
            # Try to return the path relative to project_root
            if self.request and getattr(self.request, 'website', None):
                filepath = os.path.relpath(filepath, self.request.website.project_root)
            else:
                # Fall back to returning only the last two segments
                filepath = os.sep.join(filepath.split(os.sep)[-2:])
            self.whence_raised = (filepath, frame.f_lineno)
        return self.whence_raised

    def success(self, code=200, msg=''):
        """Set :attr:`self.code` and :attr:`self.body`, then return :obj:`self`.

        Example:

        >>> raise Response().success(202, "Your request is being processed.")
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 202 Accepted: Your request is being processed.

        """
        self.code = code
        self.body = msg
        return self

    @property
    def text(self):
        """Return the response's body as a string.

        This is meant to be used in tests.
        """
        body = self.body
        if isinstance(body, str):
            return body
        if getattr(self, 'website', None):
            codec = self.website.request_processor.encode_output_as
        else:
            codec = 'utf8'
        if isinstance(body, bytes):
            return body.decode(codec)
        return ''.join(
            chunk.decode(codec) if isinstance(chunk, bytes) else chunk
            for chunk in body
        )
