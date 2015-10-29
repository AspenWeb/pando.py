"""
aspen.http.baseheaders
~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from .. import six
from .mapping import CaseInsensitiveMapping
from ..utils import typecheck


def _check_for_CRLF(value):
    """CRLF injection allows an attacker to insert arbitrary headers.

    http://www.acunetix.com/websitesecurity/crlf-injection/
    https://github.com/gratipay/security-qf35us/issues/1

    """
    if b'\r' in value or b'\n' in value:
        from aspen.exceptions import CRLFInjection
        raise CRLFInjection()


class BaseHeaders(CaseInsensitiveMapping):
    """Represent the headers in an HTTP Request or Response message.
       http://stackoverflow.com/questions/5423223/how-to-send-non-english-unicode-string-using-http-header
       and http://stackoverflow.com/questions/4400678/http-header-should-use-what-character-encoding
       have good notes on why we do everything as pure bytes here
    """

    def __init__(self, d):
        """Takes headers as a dict or str.
        """
        typecheck(d, (dict, str))
        if isinstance(d, str):
            from aspen.exceptions import MalformedHeader

            def genheaders():
                for line in d.splitlines():
                    if b':' not in line:
                        # no colon separator in header
                        raise MalformedHeader(line)
                    k, v = line.split(b':', 1)
                    if k != k.strip():
                        # disallowed leading or trailing whitspace
                        # (per http://tools.ietf.org/html/rfc7230#section-3.2.4)
                        raise MalformedHeader(line)
                    yield k, v.strip()
        else:
            genheaders = d.iteritems
        CaseInsensitiveMapping.__init__(self, genheaders)

        # Cookie
        # ======

        self.cookie = six.moves.http_cookies.SimpleCookie()
        try:
            self.cookie.load(self.get('Cookie', b''))
        except six.moves.http_cookies.CookieError:
            pass  # XXX really?


    def __setitem__(self, name, value):
        _check_for_CRLF(value)
        super(BaseHeaders, self).__setitem__(name, value)

    def add(self, name, value):
        _check_for_CRLF(value)
        super(BaseHeaders, self).add(name, value)


    def raw(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self.iteritems():
            for value in values:
                out.append(b'%s: %s' % (header, value))
        return b'\r\n'.join(out)
    raw = property(raw)
