import datetime
import logging
import os
import re
import sys
import traceback
import urlparse
from os.path import join, isfile

from aspen import http, gauntlet, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from aspen.configuration import Configurable


log = logging.getLogger('aspen.website')


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and also knows how to start
    and stop a server, *and* how to handle HTTP requests (per WSGI). It is
    available to user-developers inside of their simplates and hooks.

    """

    def __init__(self, argv=None):
        """Takes an argv list, without the initial executable name.
        """
        self.configure(argv)
        log.info("Aspen website loaded from %s." % self.root)
    
    def __call__(self, environ, start_response):
        """WSGI interface.
        """
        request = Request.from_wsgi(environ) # too big to fail :-/
        response = self.handle(request)
        response.request = request # Stick this on here at the last minute
                                   # in order to support close hooks.
        return response(environ, start_response)

    def start(self):
        log.info("Starting up Aspen website.")
        self.run_hook('startup')
        self.engine.start()

    def stop(self):
        log.info("Shutting down Aspen website.")
        self.run_hook('shutdown')
        self.engine.stop()

    def run_hook(self, name):
        self.hooks.run(name, self)

    def handle(self, request):
        """Given an Aspen request, return an Aspen response.

        Aspen uses Resource subclasses to generate responses. See
        aspen/resources/__init__.py.

        """
        try:
            try:
                self.copy_configuration_to(request)
                request.website = self

                self.hooks.run('inbound_early', request)
                gauntlet.run(request) # sets request.fs
                request.socket = sockets.get(request)
                self.hooks.run('inbound_late', request)

                # Look for a Socket.IO socket (http://socket.io/).
                if isinstance(request.socket, Response):    # handshake
                    response = request.socket
                    request.socket = None
                elif request.socket is None:                # non-socket
                    request.resource = resources.get(request)
                    response = request.resource.respond(request)
                else:                                       # socket
                    response = request.socket.respond(request)
            except:
                response = self.handle_error_nicely(request)
        except Response, response:
            # Grab the response object in the case where it was raised.  In the
            # case where it was returned, response is set in a try block above.
            pass
        else:
            # If the response object is coming from handle_error via except 
            # Response, then it already has request on it and the early hooks
            # have already been run. If it fell off the edge un-exceptionally,
            # we need to take care of those two things.
            response.request = request
            self.hooks.run('outbound_early', response)

        self.hooks.run('outbound_late', response)
        self.log_access(request, response) # TODO is this at the right level?
        return response

    def handle_error_nicely(self, request):
        """Try to provide some nice error handling.
        """
        try:                        # nice error messages
            tb_1 = traceback.format_exc()
            response = sys.exc_info()[1]
            if not isinstance(response, Response):
                log.error(tb_1)
                response = Response(500, tb_1)
            elif 200 <= response.code < 300:
                return response
            response.request = request
            self.hooks.run('outbound_early', response)
            fs = self.ours_or_theirs(str(response.code) + '.html')
            if fs is None:
                fs = self.ours_or_theirs('error.html')
            if fs is None:
                raise
            request.fs = fs
            request.original_resource = request.resource
            request.resource = resources.get(request)
            response = request.resource.respond(request, response)
            return response
        except Response, response:  # no nice error template available
            raise
        except:                     # last chance for tracebacks in the browser
            tb_2 = traceback.format_exc().strip()
            tbs = '\n\n'.join([tb_2, "... while handling ...", tb_1])
            log.error(tbs)
            if self.show_tracebacks:
                response = Response(500, tbs)
            else:
                response = Response(500)
            response.request = request
            raise response

    def find_ours(self, filename):
        """Given a filename, return a filepath.
        """
        return join(os.path.dirname(__file__), 'www', filename)

    def ours_or_theirs(self, filename):
        """Given a filename, return a filepath or None.
        """
        ours = self.find_ours(filename)
        theirs = join(self.root, '.aspen', filename)
        if isfile(theirs):
            out = theirs
        elif isfile(ours):
            out = ours
        else:
            out = None
        return out

    def log_access(self, request, response):
        """Log access.
        """

        # What was the URL path translated to?
        # ====================================

        fs = request.fs[len(self.root):]
        if fs:
            fs = '.'+fs
        else:
            fs = request.fs
        log.info("%s => %s" % (request.path.raw, fs))


        # Where was response raised from?
        # ===============================

        tb = sys.exc_info()[2]
        if tb is None:
            log.info("%33s" % '<%s>' % response)
        else:
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            co = tb.tb_frame.f_code
            filename = tb.tb_frame.f_code.co_filename
            if filename.startswith(self.root):
                filename = '.'+filename[len(self.root):]
            log.info("%33s  %s:%d" % ( '<%s>' % response
                                     , filename
                                     , frame.f_lineno
                                      ))
