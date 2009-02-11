"""Define a handler that serves static files.
"""
import datetime
import mimetypes
import rfc822
import os
import stat
import time

from aspen import mode, configuration
from aspen.exceptions import ConfigError
from aspen.handlers.autoindex import wsgi as autoindex_handler
from aspen.handlers.http import HTTP403


# WSGI callable
# =============

class WSGI(object):

    def __init__(self):
        """Hide global conf access to avoid triggering on import. See issue 137.
        """

        # Configure directory browsing.
        # =============================
        # @@: Also, this validation crap should be abstracted at some point.
        
        autoindex = configuration.conf.static.get('autoindex', None)
        if autoindex is None:
            autoindex = True # default
        elif autoindex.lower() == 'yes':
            autoindex = True
        elif autoindex.lower() == 'no':
            autoindex = False
        else:
            raise ConfigError( "autoindex must be 'yes' or 'no'"
                             , "__/etc/aspen.conf"
                             , -1 # lineno
                              )
        self.directory = autoindex and autoindex_handler or HTTP403


    def __call__(self, environ, start_response):
        """Serve a static file off of the filesystem.
    
        In staging and deployment modes, we honor any 'If-Modified-Since'
        header, an HTTP header used for caching.
    
        XXX: look at Luke Arno's ACK GPL and some others ... Etags? Iteration?
    
        """
    
        path = environ['PATH_TRANSLATED']
        if not os.path.exists(path):
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return ['Resource not found.']
        elif os.path.isdir(path):
            return self.directory(environ, start_response)
        else:
            assert os.path.isfile(path) # sanity check
    
    
        # Get basic info from the filesystem and start building a response.
        # =================================================================
    
        stats = os.stat(path)
        mtime = stats[stat.ST_MTIME]
        size = stats[stat.ST_SIZE]
        content_type = mimetypes.guess_type(path)[0] or 'text/plain'
    
    
        # Support 304s, but only in staging and production modes.
        # =======================================================
    
        status = '200 OK'
        if mode.stprod:
            ims = environ.get('HTTP_IF_MODIFIED_SINCE', '')
            if ims:
                mod_since = rfc822.parsedate(ims)
                last_modified = time.gmtime(mtime)
                if last_modified[:6] <= mod_since[:6]:
                    status = '304 Not Modified'
    
    
        # Set up the response.
        # ====================
    
        headers = []
        headers.append(('Last-Modified', rfc822.formatdate(mtime)))
        headers.append(('Content-Type', content_type))
        headers.append(('Content-Length', str(size)))
    
        start_response(status, headers)
        if status == '304 Not Modified':
            return []
        else:
            return open(path, 'rb') # need 'rb' for Windows (issue 92)


wsgi = WSGI() # singleton

