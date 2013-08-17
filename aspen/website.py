import datetime
import os
import sys
import traceback
from os.path import join, isfile
from first import first

import aspen
from aspen import dispatcher, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from aspen.configuration import Configurable
from aspen.utils import to_rfc822, utc

# 2006-11-17 was the first release of aspen - v0.3
THE_PAST = to_rfc822(datetime.datetime(2006, 11, 17, tzinfo=utc))


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
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """WSGI interface.

        Wrap this method instead of the website object itself
        when to use WSGI middleware::

            website = Website()
            website.wsgi_app = WSGIMiddleware(website.wsgi_app)

        """
        request = Request.from_wsgi(environ) # too big to fail :-/
        request.website = self
        response = self.handle_safely(request)
        response.request = request # Stick this on here at the last minute
                                   # in order to support close hooks.
        return response(environ, start_response)


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


    # Request Handling
    # ================

    def handle_safely(self, request):
        """Given an Aspen request, return an Aspen response.
        """
        try:
            request = self.do_inbound(request)
            response = self.handle(request)
        except:
            response = self.handle_error(request)

        response = self.do_outbound(response)
        return response


    def handle(self, request):
        """Given an Aspen request, return an Aspen response.

        By default we use Resource subclasses to generate responses from
        simplates on the filesystem. See aspen/resources/__init__.py.

        You can monkey-patch this method to implement single-page web apps or
        other things in configure-aspen.py:

            from aspen import Response

            def greetings_program(website, request):
                return Response(200, "Greetings, program!")

            website.handle = greetings_program

        Unusual but allowed.

        """
        # Look for a Socket.IO socket (http://socket.io/).
        if isinstance(request.socket, Response):    # handshake
            response = request.socket
            request.socket = None
        elif request.socket is None:                # non-socket
            request.resource = resources.get(request)
            response = request.resource.respond(request)
        else:                                       # socket
            response = request.socket.respond(request)
        response.request = request
        return response


    # Inbound
    # =======

    def do_inbound(self, request):
        request = self.hooks.run('inbound_early', request)
        request = self.hooks.run('inbound_core', request)
        request = self.hooks.run('inbound_late', request)
        return request

    def reset_inbound_core(self):
        self.hooks.inbound_core = [ self.set_fs_etc
                                  , self.set_socket
                                   ]

    def set_fs_etc(self, request):
        dispatcher.dispatch(request)  # mutates request

    def set_socket(self, request):
        request.socket = sockets.get(request)


    # Error
    # =====

    def handle_error(self, request):
        """Given a request, return a response.
        """
        try:                        # nice error messages
            tb_1 = traceback.format_exc()
            request = self.hooks.run('error_early', request)
            response = self.handle_error_nicely(tb_1, request)
        except Response, response:  # error simplate raised Response
            pass
        except:                     # last chance for tracebacks in the browser
            response = self.handle_error_at_all(tb_1)

        response.request = request
        response = self.hooks.run('error_late', response)
        return response


    def handle_error_nicely(self, tb_1, request):

        response = sys.exc_info()[1]

        if not isinstance(response, Response):

            # We have a true Exception; convert it to a Response object.

            response = Response(500, tb_1)
            response.request = request

        if 200 <= response.code < 300:

            # The app raised a Response(2xx). Act as if nothing
            # happened. This is unusual but allowed.

            pass

        else:

            # Delegate to any error simplate.
            # ===============================

            rc = str(response.code)
            possibles = [ rc + ".html", rc + ".html.spt", "error.html", "error.html.spt" ]
            fs = first( self.ours_or_theirs(errpage) for errpage in possibles )

            if fs is not None:
                request.fs = fs
                request.original_resource = request.resource
                request.resource = resources.get(request)
                response = request.resource.respond(request, response)

        return response


    def handle_error_at_all(self, tb_1):
        tb_2 = traceback.format_exc().strip()
        tbs = '\n\n'.join([tb_2, "... while handling ...", tb_1])
        aspen.log_dammit(tbs)
        if self.show_tracebacks:
            response = Response(500, tbs)
        else:
            response = Response(500)
        return response


    # Outbound
    # ========

    def do_outbound(self, response):
        response = self.hooks.run('outbound', response)
        return response

    def reset_outbound(self):
        self.hooks.outbound = [self.log_access]

    def log_access(self, response):
        """Log access. With our own format (not Apache's).
        """

        if self.logging_threshold > 0: # short-circuit
            return


        # What was the URL path translated to?
        # ====================================

        fs = getattr(response.request, 'fs', '')
        if fs.startswith(self.www_root):
            fs = fs[len(self.www_root):]
            if fs:
                fs = '.'+fs
        else:
            fs = '...' + fs[-21:]
        msg = "%-24s %s" % (response.request.line.uri.path.raw, fs)


        # Where was response raised from?
        # ===============================

        filename, linenum = response.whence_raised()
        if filename is not None:
            response = "%s (%s:%d)" % (response, filename, linenum)
        else:
            response = str(response)

        # Log it.
        # =======

        aspen.log("%-36s %s" % (response, msg))


    # File Resolution
    # ===============

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


    # Conveniences for testing
    # ========================
    # XXX Sure seems like this class should be refactored so we use the same
    # code for both testing and production here.

    def serve_request(self, path):
        """Given an URL path, return response.
        """
        request = Request(uri=path)
        request.website = self
        response = self.handle_safely(request)
        return response


    def load_simplate(self, path, request=None, return_request_too=False):
        """Given an URL path, return a simplate (Resource) object.
        """
        if request is None:
            request = Request(uri=path)
        if not hasattr(request, 'website'):
            request.website = self
        self.do_inbound(request)
        resource = resources.get(request)
        if return_request_too:
            return resource, request
        else:
            return resource


    def exec_simplate(self, path="/", request=None, response=None):
        """Given the URL path of a simplate, exec page two and return response.
        """
        resource, request = self.load_simplate(path, request, True)
        if response is None:
            response = Response(charset=self.charset_dynamic)
        context = resource.populate_context(request, response)
        exec resource.pages[1] in context  # let's let exceptions raise
        return response, context
