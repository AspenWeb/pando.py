"""URL rewriter for Aspen.

This module rewrites URLs based on request.path, where "route" means to alter
request.path and set a bunch of extra keys in environ. The file
,aspen/etc/routes.conf defines the routing configuration, with each line
containing one or two whitespace-separated tokens. The first token is a regular
expression to match against the incoming PATH_INFO. The second token, if
present, is the new request.path. If there is no second token, then any
matching requests will be permanently redirected to request.path plus a
trailing slash. Processing stops with the first match.

TODO: Sugar:
    /:foo/          foo.html
    =>
    /<?P(foo)[/^]+
    /<?P(foo)[/^]+/ foo.html

Groups matched in the regular expression are added to a dictionary at
request.urls.path.

By default, any direct requests for a path mentioned as a second token in
routes.conf will be responded to with 404. Use the A flag to [A]llow access.

"""
import logging
import os
import re
from os.path import isfile, join

import aspen
from aspen import restarter
from aspen.configuration.exceptions import ConfFileError
from aspen.http import Response


class Mapping(object):

    def __init__(self, pattern, path, flags):
        """Takes a regular expression pattern, a path, and flags.
        """
        self.pattern = re.compile(pattern)
        self.path = path
        self.flags

    def match(self, path):
        """Given a path, return a dictionary or None.

        The dictionary returned has keys corresponding to the named and unnamed
        groups in the match. Unnamed groups are keyed to their index as
        strings.

        """
        out = None
        match = self.pattern.match(path)
        if match is not None:
            matches = True
            out = match.groupdict()
            i = 0
            for group in match.groups():
                out[str(i)] = group
                i += 1
        return out 


# Startup Hook
# ============

mappings = []
protected = []

def startup(website):
    """Given a Website, configure the rewrite module.
    """

    confpath = join(website.root, '.aspen', 'etc', 'rewrite.conf')
    if not isfile(confpath):
        logging.info("No rewrite.conf")
    else:
        restarter.add(confpath)
        i = 0
        for line in open(confpath):
            i += 1
            line = line.split('#')[0].strip()
            if not line:
                continue

            parts = line.split() 
            nparts = len(parts)
            try:
                assert nparts in [1,2,3]
                if nparts == 1:     # will redirect to trailing slash
                    pattern = parts[0]
                    path = flags = ''
                elif nparts == 2:   # will serve new path
                    pattern, path = parts
                    flags = ''
                else:
                    assert nparts == 3 # sanity check
                    pattern, path, flags = parts
                    assert flags.startswith('[')
                    assert flags.endswith(']')
                    flags = flags[1:-1]
            except AssertionError:
                raise ConfFileError("Malformed line.", "rewrite.conf", i)

            mapping = Mapping(pattern, path, flags)
            mappings.append(mapping)
            if 'A' not in flags:
                protected.append(path)


# Inbound Hook
# ============

def inbound(request):
    path = request.path
    if path in protected:                       # protect direct access
        raise Response(404)
    for mapping in mappings:                    # look for a match
        match = mapping.match(path)
        if match is not None:
            request.original_path = path
            if mapping.path == '':              # redirect to trailing slash
                raise Response(301, headers={'Location': path+'/'}) #TODO qs
            else:                               # serve with explicit path
                request.path = mapping.path
            groups = match.groups()
            for key in range(len(groups)):      # add [i] indices to url
                val = groups[key]
                if val is None:
                    val = ''
                request.url[key] = val
            named = match.groupdict.items()
            for key, val in named:              # add ['name'] indices to url
                if val is None:
                    val = ''
                request.url[key] = val
            break                               # quit matching after first hit
