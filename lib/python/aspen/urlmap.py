"""URL routing helper for Aspen.

This module defines a middleware (called 'middleware') that routes URLs based
on PATH_INFO, where "route" means to alter PATH_INFO and set a bunch of extra
keys in environ. The file __/etc/urlmap.conf defines the routing configuration,
with each line containing one or two whitespace-separated tokens. The first
token is a regular expression to match against the incoming PATH_INFO. The
second token, if present, is the new PATH_INFO. If there is no second token,
then any matching requests will be permanently redirected to PATH_INFO plus a
trailing slash. Processing stops with the first match.

Groups matched in the regular expression are added to the WSGI environ. All
groups area available using the string of their index in the pattern;
additionally, named groups are available under their name. All names (explicit
or indexed) are prefixed with 'urlmap.'. You can change this prefix by setting
the 'prefix' knob in a [urlmap] section of __/etc/aspen.conf.

By default, any direct requests for a PATH_INFO mentioned as a second token in
urlmap.conf will be responded to with 404. This behavior can be overridden by
setting the 'allow_direct' knob in aspen.conf to any value.

This module was inspired by Django's urls.py routing.

"""
import logging
import os
import re

import aspen
from aspen import ConfigurationError, restarter
from aspen.middleware import raised


class Mapping(object):

    def __init__(self, pattern, pinfo):
        """Takes a regular expression pattern and a PATH_INFO.
        """
        self.pattern = re.compile(pattern)
        self.pinfo = pinfo

    def match(self, pinfo):
        """Given a PATH_INFO, return a dictionary or None.

        The dictionary returned has keys corresponding to the named and unnamed
        groups in the match. Unnamed groups are keyed to their index as strings.

        """
        out = None
        match = self.pattern.match(pinfo)
        if match is not None:
            matches = True
            out = match.groupdict()
            i = 0
            for group in match.groups():
                out[str(i)] = group
                i += 1
        return out 


def middleware(next):

    # Read in URL mappings.
    # =====================

    mappings = list()
    endpoints = list()
    confpath = os.path.join(aspen.paths.__, 'etc', 'urlmap.conf')
    if not os.path.isfile(confpath):
        logging.info("No urlmap.conf")
    else:
        restarter.track(confpath)
        i = 0
        for line in open(confpath):
            i += 1
            line = line.split('#')[0].strip()
            if not line:
                continue

            parts = line.split() 
            if len(parts) == 1:     # will redirect to trailing slash
                pattern = parts[0]
                pinfo = ''
            elif len(parts) == 2:   # will serve new pinfo
                pattern, pinfo = parts
            else:
                raise ConfigurationError("Malformed line %d of urlmap.conf" % i)

            mapping = Mapping(pattern, pinfo)
            mappings.append(mapping)
            endpoints.append(pinfo)


    # Get additional configuration.
    # =============================

    config = aspen.conf.urlmap
    prefix = config.get('prefix', 'urlmap')
    allow_direct = 'allow_direct' in config
    if allow_direct:
        endpoints = []


    # Define the WSGI callable.
    # =========================

    def wsgi(environ, start_response):
        pinfo = environ['PATH_INFO']
        if pinfo in endpoints:                      # protect direct access
            raise raised.Response(404)
        if pinfo.endswith('/'):                     # deal with ///// insanity
            sane_pinfo = pinfo.rstrip('/') + '/'
            if pinfo != sane_pinfo:
                raise raised.Response(301, [('Location', sane_pinfo)])
        for mapping in mappings:                    # look for a match
            match = mapping.match(pinfo)
            if match is not None:
                environ[prefix+'PATH_INFO'] = pinfo
                if mapping.pinfo == '': # redirect to trailing slash
                    raise raised.Response(301, [('Location', pinfo+'/')])
                else:                   # serve with explicit pinfo
                    environ['PATH_INFO'] = mapping.pinfo
                for key, val in match.items():
                    if val is None:
                        val = ''
                    environ[prefix+key] = val
                break # quit matching after first hit
        return next(environ, start_response)
    return wsgi

