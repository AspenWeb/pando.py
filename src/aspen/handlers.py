"""A few default handlers for aspen.
"""
import mimetypes
import rfc822
import os
import stat
import traceback
from email import message_from_file, message_from_string

from aspen import mode
from aspen.utils import is_valid_identifier


# A couple simple handlers.
# =========================

def HTTP404(environ, start_response):
    start_response('404 Not Found', [])
    return ['Resource not found.']


def pyscript(environ, start_response):
    """Execute the script pseudo-CGI-style.
    """
    context = dict()
    context['environ'] = environ
    context['start_response'] = start_response
    context['response'] = []
    context['__file__'] = environ['aspen.fp'].name

    fp = environ['aspen.fp']
    del environ['aspen.fp']

    try:
        exec fp in context
        response = context['response']
    except SystemExit:
        pass
#    except:
#        start_response( '500 Internal Server Error'
#                      , [('Content-type', 'text/plain')]
#                       )
#        if mode.debdev:
#            return [traceback.format_exc()]
#        else:
#            return ['Internal Server Error']

    return response


# A moderately complex one.
# =========================
# XXX: look at Luke Arno's ACK GPL and some others ... Etags? Iteration?

def static(environ, start_response):
    """Serve a static file off of the filesystem.

    In staging and deployment modes, we honor any 'If-Modified-Since'
    header, an HTTP header used for caching.

    """

    path = environ['PATH_TRANSLATED']
    ims = environ.get('HTTP_IF_MODIFIED_SINCE', '')


    # Get basic info from the filesystem and start building a response.
    # =================================================================

    stats = os.stat(path)
    mtime = stats[stat.ST_MTIME]
    size = stats[stat.ST_SIZE]
    content_type = mimetypes.guess_type(path)[0] or 'text/plain'


    # Support 304s, but only in deployment mode.
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
