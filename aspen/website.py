from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os

import aspen
from aspen.configuration import Configurable
from aspen.flow import Flow
from aspen.utils import to_rfc822, utc

# 2006-11-17 was the first release of aspen - v0.3
THE_PAST = to_rfc822(datetime.datetime(2006, 11, 17, tzinfo=utc))


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and also knows how to start
    and stop a server, *and* how to handle HTTP requests (per WSGI). It is
    available to user-developers inside of their simplates and hooks.

    """

    def __init__(self, argv=None):
        """Takes an argv list, without the initial executable name.
        """
        self.flow = Flow('aspen.flows.request')
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


    def respond(self, environ, _run_through=None):
        """Given a WSGI environ, return a state dict.
        """

        state = {}
        state['website'] = self
        state['environ'] = environ

        state = self.flow.run(state, through=_run_through)

        return state


    # Interface for Server
    # ====================

    def start(self):
        aspen.log_dammit("Starting up Aspen website.")
        self.hooks.run('startup', self)
        self.network_engine.start()

    def stop(self):
        aspen.log_dammit("Shutting down Aspen website.")
        self.hooks.run('shutdown', self)
        self.network_engine.stop()


    # File Resolution
    # ===============

    def find_ours(self, filename):
        """Given a filename, return a filepath.
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
