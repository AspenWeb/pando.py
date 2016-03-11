"""
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import cgi
import urllib

from .mapping import Mapping


class PathPart(unicode):
    """A string with a mapping for extra data about it."""

    __slots__ = ['params']

    def __new__(cls, value, params):
        obj = super(PathPart, cls).__new__(cls, value)
        obj.params = params
        return obj


class Path(Mapping):
    """Represent the path of a resource.

    This is populated by aspen.gauntlet.virtual_paths.

    """

    def __init__(self, raw):
        self.raw = raw
        self.decoded = urllib.unquote(raw).decode('UTF-8')
        self.parts = extract_rfc2396_params(raw)


def extract_rfc2396_params(path):
    """RFC2396 section 3.3 says that path components of a URI can have
    'a sequence of parameters, indicated by the semicolon ";" character.'
    and that ' Within a path segment, the characters "/", ";", "=", and
    "?" are reserved.'  This way you can do
    /frisbee;color=red;size=small/logo;sponsor=w3c;color=black/image.jpg
    and each path segment gets its own params.

    * path should be raw so we don't split or operate on a decoded character
    * output is decoded
    """
    pathsegs = path.lstrip(b'/').split(b'/')
    def decode(input):
        return urllib.unquote(input).decode('UTF-8')

    segments_with_params = []
    for component in pathsegs:
        parts = component.split(b';')
        params = Mapping()
        segment = decode(parts[0])
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split(b'=', 1)
            else:
                k, v = p, b''
            params.add(decode(k), decode(v))
        segments_with_params.append(PathPart(segment, params))
    return segments_with_params


class Querystring(Mapping):
    """Represent an HTTP querystring.
    """

    def __init__(self, raw):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.decoded = urllib.unquote_plus(raw).decode('UTF-8')
        self.raw = raw

        # parse_qs does its own unquote_plus'ing ...
        as_dict = cgi.parse_qs( raw
                              , keep_blank_values = True
                              , strict_parsing = False
                               )

        # ... but doesn't decode to unicode.
        for k, vals in as_dict.items():
            as_dict[k.decode('UTF-8')] = [v.decode('UTF-8') for v in vals]

        Mapping.__init__(self, as_dict)
