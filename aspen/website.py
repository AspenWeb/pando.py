import os
import sys
import traceback
from os.path import join, isfile

import aspen
from aspen import gauntlet, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from aspen.configuration import Configurable


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and also knows how to start
    and stop a server, *and* how to handle HTTP requests (per WSGI). It is
    available to user-developers inside of their resources and hooks.

    """

    def __init__(self, argv=None):
        """Takes an argv list, without the initial executable name.
        """
        self.configure(argv)
    
    def __call__(self, environ, start_response):
        """WSGI interface.
        """
        request = Request.from_wsgi(environ) # too big to fail :-/
        response = self.handle(request)
        response.request = request # Stick this on here at the last minute
                                   # in order to support close hooks.
        return response(environ, start_response)

    def start(self):
        aspen.log_dammit("Starting up Aspen website.")
        self.hooks.startup.run(self)
        self.network_engine.start()

    def stop(self):
        aspen.log_dammit("Shutting down Aspen website.")
        self.hooks.shutdown.run(self)
        self.network_engine.stop()

    def handle(self, request):
        """Given an Aspen request, return an Aspen response.

        Aspen uses Resource subclasses to generate responses. See
        aspen/resources/__init__.py.

        """
        try:
            try:
                #self.copy_configuration_to(request)
                request.website = self

                self.hooks.inbound_early.run(request)
                gauntlet.run(request) # sets request.fs
                request.socket = sockets.get(request)
                self.hooks.inbound_late.run(request)

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
            self.hooks.outbound_early.run(response)

        self.hooks.outbound_late.run(response)
        self.log_access(request, response) # TODO is this at the right level?
        return response

    def handle_error_nicely(self, request):
        """Try to provide some nice error handling.
        """
        try:                        # nice error messages
            tb_1 = traceback.format_exc()
            response = sys.exc_info()[1]
            if not isinstance(response, Response):
                aspen.log_dammit(tb_1)
                response = Response(500, tb_1)
            elif 200 <= response.code < 300:
                return response
            response.request = request
            self.hooks.outbound_early.run(response)
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
            aspen.log_dammit(tbs)
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
        if self.project_root is not None:
            theirs = join(self.project_root, filename)
            if isfile(theirs):
                return theirs

        ours = self.find_ours(filename)
        if isfile(ours):
            return ours

        return None

    def log_access(self, request, response):
        """Log access. With our own format (not Apache's).
        """

        if self.logging_threshold > 0: # short-circuit
            return


        # What was the URL path translated to?
        # ====================================

        fs = request.fs
        if fs.startswith(self.www_root):
            fs = fs[len(self.www_root):]
            if fs:
                fs = '.'+fs
        else:
            fs = '...' + fs[-21:]
        msg = "%-24s %s" % (request.line.uri.path.raw, fs)


        # Where was response raised from?
        # ===============================

        tb = sys.exc_info()[2]
        if tb is not None:
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            filename = tb.tb_frame.f_code.co_filename.split(os.sep)[-1]
            response = "%s (%s:%d)" % (response, filename, frame.f_lineno)
        else:
            response = str(response)


        # Log it.
        # =======

        aspen.log("%-36s %s" % (response, msg))
