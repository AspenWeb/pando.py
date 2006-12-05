"""A few default handlers for aspen.
"""
import mimetypes
import rfc822
import os
import stat
import traceback
from datetime import datetime
from email import message_from_file, message_from_string
from os.path import isdir, isfile, join

from aspen import mode, __version__
from aspen.utils import is_valid_identifier


# File or Directory
# =================

def HTTP404(environ, start_response):
    start_response('404 Not Found', [])
    return ['Resource not found.']


# File Handlers
# =============

def pyscript(environ, start_response):
    """Execute the script pseudo-CGI-style.
    """
    path = environ['PATH_TRANSLATED']
    assert isfile(path)

    context = dict()
    context['environ'] = environ
    context['start_response'] = start_response
    context['response'] = []
    context['__file__'] = path

    try:
        exec open(path) in context
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


def static(environ, start_response):
    """Serve a static file off of the filesystem.

    In staging and deployment modes, we honor any 'If-Modified-Since'
    header, an HTTP header used for caching.

    XXX: look at Luke Arno's ACK GPL and some others ... Etags? Iteration?

    """
    assert isfile(environ['PATH_TRANSLATED'])

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


# Directory Handlers
# ==================

STYLE = """\

body {font-family: "Trebuchet MS", sans-serif;}
table {font-family: monospace;}
.dir {font-weight: bold;}
.file {}
td {padding: 0 1em 0 0;}
td.size {text-align: right;}
th {text-align: left;}
tr.even {background: #eee;}
tr:hover {background: #eef;}

"""

KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024
PB = TB * 1024
EB = PB * 1024

def _get_size(stats):
    """Given a stat struct, return a size string.
    """
    size = float(stats[stat.ST_SIZE])
    if size < KB:
        return '%d &nbsp;B' % (size)
    elif size < MB:
        return '%d kB' % (size / KB)
    elif size < GB:
        return '%d MB' % (size / MB)
    elif size < TB:
        return '%d GB' % (size / GB)
    elif size < PB:
        return '%d TB' % (size / TB) # :^)
    elif size < EB:
        return '%d PB' % (size / PB) # :^D
    else:
        return '%d EB' % (size / EB) # 8^D


def _get_time(stats):
    """Given a stat struct, return a date stamp string.
    """
    return str(datetime.fromtimestamp(stats[stat.ST_MTIME]))


def autoindex(environ, start_response):
    """Serve an automatic index for a directory.
    """
    fspath = environ['PATH_TRANSLATED']
    assert isdir(fspath)

    root = environ['aspen.website'].config.paths.root
    urlpath = fspath[len(root):]
    urlpath = '/'.join(urlpath.split(os.sep))
    title = urlpath and urlpath or '/'


    # Gather dirs, files, and others under this directory.
    # ====================================================
    # We have to loop twice in order to guarantee sorted output.

    dirs = []
    files = []
    others = []
    for name in os.listdir(fspath):
        _fspath = os.path.join(fspath, name)
        _urlpath = '/'.join([urlpath, name])
        x = (_fspath, _urlpath, name)
        el = others
        if isdir(_fspath):
            el = dirs
        elif isfile(_fspath):
            el = files
        el.append(x)
    dirs.sort()
    files.sort()
    others.sort()


    # Generate the HTML.
    # ==================

    out = ['<html><head><title>%s</title>' % title]
    def a(s):
        out.append(s + '\r\n')
    a('<style>%s</style></head><body>' % STYLE)
    a('<h1>%s</h1>' % title)
    a('<table>')
    a('<tr><th class="name">Name</th><th>Size</th><th>Last Modified</th></tr>')

    i = 0
    if environ['PATH_TRANSLATED'] != root:
        a('<tr><td class="odd"><a href="../">../</a></td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        i += 1

    for el in (dirs, files, others):
        for _fspath, _urlpath, name in el:
            stats = os.stat(_fspath)
            a('<tr class="%s">' % ((i%2) and 'even' or 'odd'))
            if isdir(_fspath):
                a('  <td class="dir"><a href="%s">%s/</a></td>' % (_urlpath, name))
                a('  <td>&nbsp;</td>')
            elif isfile(_fspath):
                a('  <td class="file"><a href="%s">%s</a></td>' % (_urlpath, name))
                a('  <td class="size">%s</td>' % _get_size(stats))
            else:
                a('  <td class="other">%s</li>' % name)
                a('  <td>&nbsp;</td>')
            a('  <td class="modtime">%s</td>' % _get_time(stats))
            a('</tr>')
            i += 1

    a('</table>')
    a('<hr /><i>Generated by <a href="http://www.zetadev.com/software/aspen/">')
    a('Aspen %s</a>' % __version__)
    a('</body></html>')


    # Send it off.
    # ============

    start_response('200 OK', [('Content-Type', 'text/html')])
    return out


def default(environ, start_response):
    """Try to serve a default resource.
    """
    path = environ['PATH_TRANSLATED']
    assert isdir(path)
    defaults = environ['aspen.website'].config.defaults
    assert defaults is not None

    default = None
    for name in defaults:
        _path = join(path, name)
        if isfile(_path):
            default = _path
            break
    if default is None:
        if 'aspen.autoindex_next' in environ:
            return None
        start_response('403 Forbidden', [])
        return ['No default resource for this directory.']
    path = environ['PATH_TRANSLATED'] = default

    new_handler = environ['aspen.website'].get_handler(path)
    return new_handler.handle(environ, start_response)


def default_or_autoindex(environ, start_response):
    """Serve a default file; failing that, an autoindex.
    """
    assert isdir(environ['PATH_TRANSLATED'])
    environ['aspen.autoindex_next'] = True
    response = default(environ, start_response)
    if response is None:
        response = autoindex(environ, start_response)
    return response
