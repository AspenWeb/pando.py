from collections import defaultdict

from aspen.http.mapping import Mapping


class BaseHeaders(Mapping):
    """Represent the headers in an HTTP Request or Response message.
    """

    def __init__(self, raw):
        """Takes headers as a string.
        """
        self.raw = raw
        Mapping.__init__(self)
        hd = defaultdict(list)
        for line in raw.splitlines():
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
        return super(BaseHeaders, self).__in__(name.lower());

    def all(self, name, default=None):
        return super(BaseHeaders, self).all(name.lower(), default);

    def one(self, name, default=None):
        return super(BaseHeaders, self).one(name.lower(), default);

    def set(self, name, value):
        return super(BaseHeaders, self).set(name.lower(), value);
