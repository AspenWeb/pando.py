"""Define a handler that generates an index for directories.
"""
import os
import stat
from datetime import datetime
from os.path import basename, isdir, isfile, join

import aspen


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
#footer {font-size: smaller; font-style: italic;}

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
        return '%d &nbsp;&nbsp;&nbsp;B' % (size)
    elif size < MB:
        return '%.1f kB' % (size / KB)
    elif size < GB:
        return '%.1f MB' % (size / MB)
    elif size < TB:
        return '%.1f GB' % (size / GB)
    elif size < PB:
        return '%.1f TB' % (size / TB) # :^)
    elif size < EB:
        return '%.1f PB' % (size / PB) # :^D
    else:
        return '%.1f EB' % (size / EB) # 8^D


def _get_time(stats):
    """Given a stat struct, return a date stamp string.
    """
    return str(datetime.fromtimestamp(stats[stat.ST_MTIME]))


def autoindex(environ, start_response):
    """Serve an automatic index for a directory.
    """
    fspath = environ['PATH_TRANSLATED']
    assert isdir(fspath) # sanity check

    root = aspen.paths.root
    urlpath = fspath[len(root):]
    urlpath = '/'.join(urlpath.split(os.sep))
    title = urlpath and urlpath or '/'


    # Gather dirs, files, and others under this directory.
    # ====================================================
    # We have to loop here and again below in order to guarantee sorted output.

    dirs = []
    files = []
    others = []
    for name in os.listdir(fspath):
        _fspath = join(fspath, name)
        if _fspath == aspen.paths.__: # don't list magic directory
            continue
        if basename(_fspath) == 'README.aspen': # nor these
            continue
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
    a('<hr /><div id="footer">This index was brought to you by')
    a('<a href="http://www.zetadev.com/software/aspen/">')
    a('Aspen v%s</a>.</div>' % aspen.__version__)
    a('</body></html>')


    # Send it off.
    # ============

    start_response('200 OK', [('Content-Type', 'text/html')])
    return out
