import cgi

from aspen.http.mapping import Mapping


class WwwForm(Mapping):
    """Represent a WWW form.
    """

    def __init__(self, s):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.raw = s
        self._dict = cgi.parse_qs( s
                                 , keep_blank_values = True
                                 , strict_parsing = False
                                  )
