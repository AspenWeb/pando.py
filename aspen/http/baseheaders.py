from collections import defaultdict

from aspen.http.mapping import CaseInsensitiveMapping


class BaseHeaders(CaseInsensitiveMapping):
    """Represent the headers in an HTTP Request or Response message.
    """

    def __init__(self, raw):
        """Takes headers as a string.
        """
        hd = defaultdict(list)
        for line in raw.splitlines():
            k, v = line.strip().split(':', 1)
            hd[k.strip().lower()].append(v.strip())
        CaseInsensitiveMapping.__init__(self, hd)

    def raw(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self._dict.iteritems():
            for value in values:
                out.append('%s: %s' % (header.title(), value))
        return '\r\n'.join(out)
    raw = property(raw)
