from aspen.http.mapping import Mapping
from diesel.protocols.http import HttpHeaders as DieselHeaders


class Headers(Mapping):
    """Represent the headers in an HTTP Request message.
    """

    def __init__(self, headers):
        """Takes headers as a string.
        """
        diesel_headers = DieselHeaders()
        diesel_headers.parse(headers)
        self._diesel_headers = diesel_headers
        Mapping.__init__(self)
        self._dict.update(diesel_headers._headers)

    def to_http(self):
        """Return the headers as a string, formatted for an HTTP message.
        """
        out = []
        for header, values in self._dict.iteritems():
            for value in values:
                out.append('%s: %s' % (header.title(), value))
        return '\r\n'.join(out)


