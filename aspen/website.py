"""
aspen.website
+++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os

from algorithm import Algorithm
from aspen.configuration import Configurable
from aspen.utils import to_rfc822, utc

# 2006-11-17 was the first release of aspen - v0.3
THE_PAST = to_rfc822(datetime.datetime(2006, 11, 17, tzinfo=utc))


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and also knows how to start
    and stop a server, *and* how to handle HTTP requests (per WSGI). It is
    available to user-developers inside of their simplates and hooks.

    """

    def __init__(self, argv=None, server_algorithm=None):
        """Takes an argv list, without the initial executable name.
        """
        self.server_algorithm = server_algorithm
        self.algorithm = Algorithm.from_dotted_name('aspen.algorithms.website')
        self.configure(argv)


    def __call__(self, environ, start_response):
        # back-compatibility for network engines
        return self.wsgi_app(environ, start_response)


    def wsgi_app(self, environ, start_response):
        """WSGI interface.

        Wrap this method (instead of the website object itself) when you want
        to use WSGI middleware::

            website = Website()
            website.wsgi = WSGIMiddleware(website.wsgi)

        """
        wsgi = self.respond(environ)['response']
        return wsgi(environ, start_response)


    def respond(self, environ, raise_immediately=None, return_after=None):
        """Given a WSGI environ, return a state dict.
        """
        return self.algorithm.run( website=self
                                 , environ=environ
                                 , _raise_immediately=raise_immediately
                                 , _return_after=return_after
                                  )


    # File Resolution
    # ===============

    def find_ours(self, filename):
        """Given a filename, return the filepath to aspen's internal version
	   of that filename.  No existence checking is done, this just abstracts
	   away the __file__ reference nastiness.
        """
        return os.path.join(os.path.dirname(__file__), 'www', filename)

    def ours_or_theirs(self, filename):
        """Given a filename, return a filepath or None.
        """
        if self.project_root is not None:
            theirs = os.path.join(self.project_root, filename)
            if os.path.isfile(theirs):
                return theirs

        ours = self.find_ours(filename)
        if os.path.isfile(ours):
            return ours

        return None
