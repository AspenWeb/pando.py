"""
aspen.website
+++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from algorithm import Algorithm
from .configuration import Configurable
from .http.response import Response
from .exceptions import BadLocation


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and how to handle HTTP
    requests (per WSGI). It is available to user-developers inside of their
    simplates and algorithm functions.

    """

    def __init__(self, **kwargs):
        """Takes configuration in kwargs.
        """
        self.algorithm = Algorithm.from_dotted_name('aspen.algorithms.website')
        self.configure(**kwargs)


    def respond(self, environ, raise_immediately=None, return_after=None):
        """Given a WSGI environ, return a state dict.
        """
        return self.algorithm.run( website=self
                                 , environ=environ
                                 , _raise_immediately=raise_immediately
                                 , _return_after=return_after
                                  )

    def redirect(self, location, code=None, permanent=False, base_url=None, response=None):
        """Raise a redirect Response.

        If code is None then it will be set to 301 (Moved Permanently) if
        permanent is True and 302 (Found) if it is False. If url doesn't start
        with base_url (defaulting to self.base_url), then we prefix it with
        base_url before redirecting. This is a protection against open
        redirects. If you wish to use a relative path or full URL as location,
        then base_url must be the empty string; if it's not, we raise
        BadLocation. If you provide your own response we will set .code and
        .headers['Location'] on it.

        """
        response = response if response else Response()
        response.code = code if code else (301 if permanent else 302)
        base_url = base_url if base_url is not None else self.base_url
        if not location.startswith(base_url):
            newloc = base_url + location
            if not location.startswith('/'):
                raise BadLocation(newloc)
            location = newloc
        response.headers['Location'] = location
        raise response
