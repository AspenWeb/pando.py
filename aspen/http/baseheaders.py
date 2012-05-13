from Cookie import CookieError, SimpleCookie

from aspen.http.mapping import CaseInsensitiveMapping


class BaseHeaders(CaseInsensitiveMapping):
    """Represent the headers in an HTTP Request or Response message.
    """

    def __init__(self, raw):
        """Takes headers as a string.
        """
        def genheaders():
            for line in raw.splitlines():
                k, v = line.split(':', 1)
                yield k.strip(), v.strip()
        CaseInsensitiveMapping.__init__(self, genheaders)
      

        # Cookie
        # ======

        self.cookie = SimpleCookie()
        try:
            self.cookie.load(self.get('Cookie', ''))
        except CookieError:
            pass # XXX really?


    def raw(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self.iteritems():
            for value in values:
                out.append('%s: %s' % (header, value))
        return '\r\n'.join(out)
    raw = property(raw)
