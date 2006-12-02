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

    def __init__(self, config):
        self.config = config


    # Main Dispatcher
    # ===============

    def __call__(self, environ, start_response):
        """Main WSGI callable.
        """

        # Translate the request to the filesystem.
        # ========================================

        fspath = translate(self.config.paths.root, environ['PATH_INFO'])
        if self.config.paths.__ is not None:
            if fspath.startswith(self.config.paths.__): # protect magic dir
                start_response('404 Not Found', [])
                return ['Resource not found.']
        environ['PATH_TRANSLATED'] = fspath


        # Dispatch to a WSGI app or an aspen handler.
        # ===========================================

        app = self.get_app(environ, start_response) # 301
        if type(app) is type([]):                           # redirection
            response = app
        elif app is not None:                               # app
            response = app(environ, start_response) # WSGI
        else:                                               # handler
            if not exists(fspath):
                start_response('404 Not Found', [])
                return ['Resource not found.']
            response = check_trailing_slash(environ, start_response)
            if response is not None:
                return response


            # Possibly find a default resource.
            # =================================

            if isdir(fspath):
                default = None
                for name in self.config.defaults:
                    _path = join(fspath, name)
                    if isfile(_path):
                        default = _path
                        break
                if default is None:
                    start_response('403 Forbidden', [])
                    return ['No default resource for this directory.']
                fspath = default


            # Dispatch to a handler.
            # ======================

            environ['PATH_TRANSLATED'] = fspath
            environ['aspen.website'] = self
            fp = environ['aspen.fp'] = open(fspath)

            handler = self.get_handler(fp)
            fp.seek(0)
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
        test_path = environ['PATH_INFO']
        if not test_path.endswith('/'):
            test_path += '/'
        for app_urlpath, _app in self.config.apps:
            if test_path.startswith(app_urlpath):
                environ['PATH_TRANSLATED'] = translate( self.config.paths.root
                                                      , app_urlpath
                                                       )
                if not isdir(environ['PATH_TRANSLATED']):
                    start_response('404 Not Found', [])
                    return ['Resource not found.']
                if app_urlpath.endswith('/'):
                    response = check_trailing_slash(environ, start_response)
                    if response is not None:
                        return response
                app = _app
                break
        if app is None:
            log.debug("No app found for '%s'" % environ['PATH_INFO'])
        return app


    def get_handler(self, fp):
        """Given a filesystem path, return the first matching handler.
        """
        for handler in self.config.handlers:
            fp.seek(0)
            if handler.match(fp):
                return handler

        log.warn("No handler found for filesystem path '%s'" % fp.name)
        raise HandlerError("No handler found.")
