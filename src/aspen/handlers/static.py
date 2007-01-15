"""Define a handler that serves static files.
"""
import mimetypes
import rfc822
import os
import stat
import time
from os.path import isfile

from aspen import mode


def static(environ, start_response):
    """Serve a static file off of the filesystem.

    In staging and deployment modes, we honor any 'If-Modified-Since'
    header, an HTTP header used for caching.

    XXX: look at Luke Arno's ACK GPL and some others ... Etags? Iteration?

    """
    assert isfile(environ['PATH_TRANSLATED']) # sanity check

    path = environ['PATH_TRANSLATED']
    ims = environ.get('HTTP_IF_MODIFIED_SINCE', '')


    # Get basic info from the filesystem and start building a response.
    # =================================================================

    stats = os.stat(path)
    mtime = stats[stat.ST_MTIME]
    size = stats[stat.ST_SIZE]
    content_type = mimetypes.guess_type(path)[0] or 'text/plain'


    # Support 304s, but only in production mode.
    # ==========================================

    status = '200 OK'
    if mode.stprod:
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
        return open(path)
