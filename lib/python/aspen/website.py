import logging
import os
import sys

import aspen
from aspen import mode
from aspen.exceptions import HandlerError
from aspen.utils import check_trailing_slash, find_default, translate


log = logging.getLogger('aspen.website')


class Website(object):
    """Represent a publication, application, or hybrid website.
    """

    def __init__(self, server):
        self.server = server
        self.configuration = server.configuration
        self.configuration.load_plugins() # user modules imported here
        self.root = self.configuration.paths.root


    # Main Dispatcher
    # ===============

    def __call__(self, environ, start_response):
        """Main WSGI callable.
        """

        # Translate the request to the filesystem.
        # ========================================

        hide = False
        fspath = translate(self.root, environ['PATH_INFO'])
        if self.configuration.paths.__ is not None:
            if fspath.startswith(self.configuration.paths.__):  # magic dir
                hide = True
        if os.path.basename(fspath) == 'README.aspen':          # README.aspen
            hide = True
        if hide:
            start_response('404 Not Found', [])
            return ['Resource not found.']
        environ['PATH_TRANSLATED'] = fspath


        # Dispatch to an app.
        # ===================

        app = self.get_app(environ, start_response) # 301
        if isinstance(app, list):                           # want redirection
            response = app
        elif app is not None:                               # have app
            response = app(environ, start_response) # WSGI
        elif not os.path.exists(fspath):                    # 404 NOT FOUND
            start_response('404 Not Found', [])
            response = ['Resource not found.']


        # Dispatch to a handler.
        # ======================

        else:                                               # handler
            response = check_trailing_slash(environ, start_response)
            if response is None: # no redirection
                fspath = find_default(self.configuration.defaults, fspath)
                environ['PATH_TRANSLATED'] = fspath
                handler = self.get_handler(fspath)
                response = handler.handle(environ, start_response) # WSGI

        return response


    # Plugin Retrievers
    # =================
    # Unlike the middleware stack, apps and handlers need to be located
    # per-request.

    def get_app(self, environ, start_response):
        """Given a WSGI environ, return the first matching app.
        """

        app = None
        path = match_against = environ['PATH_INFO']
        if not match_against.endswith('/'):
            match_against += '/'

        for app_urlpath, _app in self.configuration.apps:

            # Do basic validation.
            # ====================

            if not match_against.startswith(app_urlpath):
                continue
            environ['PATH_TRANSLATED'] = translate(self.root, app_urlpath)
            if not os.path.isdir(environ['PATH_TRANSLATED']):
                start_response('404 Not Found', [])
                return ['Resource not found.']


            # Check trailing slash.
            # =====================

            if app_urlpath.endswith('/'): # "please canonicalize"
                if path == app_urlpath[:-1]:
                    response = check_trailing_slash(environ, start_response)
                    assert response is not None # sanity check
                    return response # redirect to trailing slash
                app_urlpath = app_urlpath[:-1] # trailing slash goes in
                                               # PATH_INFO, not SCRIPT_NAME

            # Update environ.
            # ===============

            environ["SCRIPT_NAME"] = app_urlpath
            environ["PATH_INFO"] = path[len(app_urlpath):]

            app = _app
            break

        if app is None:
            log.debug("No app found for '%s'" % environ['PATH_INFO'])

        return app


    def get_handler(self, pathname):
        """Given a full pathname, return the first matching handler.
        """
        for handler in self.configuration.handlers:
            if handler.match(pathname):
                return handler

        log.warn("No handler found for filesystem path '%s'" % pathname)
        raise HandlerError("No handler found.")
