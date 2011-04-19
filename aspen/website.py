import datetime
import logging
import os
import re
import sys
import traceback
import urlparse
from os.path import join, isfile

from aspen import gauntlet, simplates
from aspen.http.request import Request
from aspen.http.response import Response


log = logging.getLogger('aspen.website')


class Website(object):
    """Represent a website.
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.conf = configuration.conf
        self.opts = self.conf.aspen
        self.root = configuration.root
        self.hooks = configuration.hooks
        self.loader = configuration.loader
        self.show_tracebacks = self.opts.no('show_tracebacks')

    def __call__(self, diesel_request):
        """Given a Diesel request, return a Diesel response.
        """
        request = Request.from_diesel(diesel_request) # too big to fail :-/
        response = self.handle(request)
        return response._to_diesel(diesel_request) # sends bits, returns bool

    def handle(self, request):
        """Given an Aspen request, return an Aspen response.
        """
        try:
            try:
                request.configuration = self.configuration
                request.conf = self.configuration.conf
                request.root = self.configuration.root
                request.website = self
                request = self.hooks.run('inbound_early', request)
                request.fs = self.translate(request)
                request = self.hooks.run('inbound_late', request)
                response = simplates.handle(request)
            except:
                response = self.handle_error_nicely(request)
        except Response, response:
            # Grab the response object in the case where it was raised.  In the
            # case where it was returned from simplates.handle, response is set
            # in a try block above.
            pass
        else:
            # If the response object is coming from handle_error via except 
            # Response, then it already has request on it and the early hooks
            # have already been run. If it fell off the edge un-exceptionally,
            # we need to take care of those two things.
            response.request = request
            self.hooks.run('outbound_early', response)

        self.hooks.run('outbound_late', response)
        response.headers.set('Content-Length', len(response.body))
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
            response.request = request
            self.hooks.run('outbound_early', response)
            fs = self.ours_or_theirs(str(response.code) + '.html')
            if fs is None:
                fs = self.ours_or_theirs('error.html')
            if fs is None:
                raise
            request.fs = fs
            response = simplates.handle(request, response)
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

    def translate(self, request):
        """Given a Request, return a filesystem path, or raise Response.
        """
       
        # First step.
        # ===========
        # Set request.fs initially, return a list of fspath parts.

        parts = gauntlet.translate(request)
        log.debug("got request for " + request.fs)


        # The Gauntlet
        # ============
        # Keep request.fs up to date for logging purposes. It is used in
        # log_access, below, which could be triggered by any of the raises
        # herein. Each of these sets request.fs, and returns None or raises.

        gauntlet.check_sanity(request)
        gauntlet.hidden_files(request)
        gauntlet.virtual_paths(request, parts)
        gauntlet.trailing_slash(request)
        gauntlet.index(request)
        gauntlet.autoindex( request
                          , self.opts.no('list_directories')
                          , self.ours_or_theirs('autoindex.html')
                           )
        gauntlet.socket_files(request)
        gauntlet.not_found(request, self.find_ours('favicon.ico'))

        
        # Now you are one of us.
        # ======================

        return request.fs

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
