from http.cookies import CookieError, SimpleCookie

from .mapping import BytesMapping, CaseInsensitiveMapping


def _check_for_CRLF(value):
    """CRLF injection allows an attacker to insert arbitrary headers.

    http://www.acunetix.com/websitesecurity/crlf-injection/
    https://github.com/gratipay/security-qf35us/issues/1

    """
    contains_crlf = (
        isinstance(value, bytes) and (b'\r' in value or b'\n' in value) or
        isinstance(value, str) and ('\r' in value or '\n' in value)
    )
    if contains_crlf:
        from pando.exceptions import CRLFInjection
        raise CRLFInjection()


class BaseHeaders(BytesMapping, CaseInsensitiveMapping):
    """Represent the headers in an HTTP Request or Response message.

    `How to send non-English unicode string using HTTP header?
    <http://stackoverflow.com/q/5423223/>`_ and
    `What character encoding should I use for a HTTP header?
    <http://stackoverflow.com/q/4400678/>`_
    have good notes on why we do everything as pure bytes here.
    """

    def __init__(self, headers=()):
        """Takes headers as a dict, or list of items.
        """
        super().__init__(headers)

        # Cookie
        # ======

        self.cookie = SimpleCookie()
        cookie = self.get(b'Cookie', b'')
        if isinstance(cookie, bytes):
            cookie = cookie.decode('ascii', 'replace')
        try:
            self.cookie.load(cookie)
        except CookieError:
            pass  # XXX really?

    def __setitem__(self, name, value):
        """Checks for CRLF in ``value``, then calls the superclass method:

        .. automethod:: pando.http.mapping.CaseInsensitiveMapping.__setitem__
        """
        _check_for_CRLF(value)
        super().__setitem__(name, value)

    def add(self, name, value):
        """Checks for CRLF in ``value``, then calls the superclass method:

        .. automethod:: pando.http.mapping.CaseInsensitiveMapping.add
        """
        _check_for_CRLF(value)
        super().add(name, value)

    @property
    def raw(self):
        """Return the headers as a bytestring, formatted for an HTTP message.
        """
        out = []
        for header, values in sorted(self.items()):
            for value in values:
                out.append(header + b': ' + value)
        return b'\r\n'.join(out)
