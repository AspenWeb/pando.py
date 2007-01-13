import logging
import os
import sys
from os.path import exists, isdir, isfile, join

from aspen import mode
from aspen.exceptions import HandlerError
from aspen.utils import check_trailing_slash, translate


log = logging.getLogger('aspen.website')


class Website:
    """Represent a publication, application, or hybrid website.
    """

    def __init__(self, configuration):
        self.configuration = configuration


    # Main Dispatcher
    # ===============

    def __call__(self, environ, start_response):
        """Main WSGI callable.
        """

        # Translate the request to the filesystem.
        # ========================================

        fspath = translate(self.configuration.paths.root, environ['PATH_INFO'])
        if self.configuration.paths.__ is not None:
            if fspath.startswith(self.configuration.paths.__): # protect magic dir
                start_response('404 Not Found', [])
                return ['Resource not found.']
        environ['PATH_TRANSLATED'] = fspath


        # Dispatch to an app.
        # ===================

        app = self.get_app(environ, start_response) # 301
        if isinstance(app, list):                           # redirection
            response = app
        elif app is not None:                               # app
            response = app(environ, start_response) # WSGI
        elif not exists(fspath):                            # 404 NOT FOUND
            start_response('404 Not Found', [])
            response = ['Resource not found.']


        # Dispatch to a handler.
        # ======================

        else:                                               # handler
            response = check_trailing_slash(environ, start_response)
            if response is None: # no redirection
                if isdir(fspath): # locate any default resource
                    default = None
                    for name in self.configuration.defaults:
                        _path = join(fspath, name)
                        if isfile(_path):
                            default = _path
                            break
                    if default is not None:
                        environ['PATH_TRANSLATED'] = fspath = default
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
        path = test_path = environ['PATH_INFO']
        if not test_path.endswith('/'):
            test_path += '/'
        for app_urlpath, _app in self.configuration.apps:
            if test_path.startswith(app_urlpath):
                environ['PATH_TRANSLATED'] = translate( self.configuration.paths.root
                                                      , app_urlpath
                                                       )
                if not isdir(environ['PATH_TRANSLATED']):
                    start_response('404 Not Found', [])
                    return ['Resource not found.']
                if app_urlpath.endswith('/'):
                    response = check_trailing_slash(environ, start_response)
                    if response is not None:
                        return response
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
