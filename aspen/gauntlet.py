"""Define a bunch of functions that change request.fs.

These functions determine the handelability of a request, and run in the order
given here.

"""
import os
import urlparse
from os.path import join, isfile, isdir, dirname, exists

from aspen import Response


def translate(request):
    """Translate urlpath to fspath, returning urlpath parts.

    We specifically avoid removing symlinks in the path so that the filepath
    remains under the website root. Also, we don't want trailing slashes for
    directories in request.fs.

    """
    parts = [request.root] + request.path.raw.lstrip('/').split('/')
    request.fs = os.sep.join(parts).rstrip(os.sep)
    return parts

def check_sanity(request):
    """Make sure the request is under our root.
    """
    if not request.fs.startswith(request.root):
        raise response(404)

def hidden_files(request):
    """Protect hidden files.
    """
    if '/.' in request.fs[len(request.root):]:
        raise Response(404)

def virtual_paths(request, parts):
    """Support /foo/bar.html => ./%blah/bar.html and /blah.html => ./%flah.html

    Parts is a list of fs path parts as returned by translate, above. 

    Path parts will end up in request.path, a dict subclass. There can only be 
    one variable per path part. If a directory has more than one subdirectory
    starting with '%' then only the 'first' is used.

    """
    if '/%' in request.fs[len(request.root):]:  # disallow direct access
        raise Response(404)
    if not exists(request.fs):
        matched = request.root
        nparts = len(parts)
        for i in range(1, nparts):
            part = parts[i]
            next = join(matched, part)
            if exists(next):    # this URL part names an actual directory
                matched = next
            else:               # this part is missing; do we have a %subdir?
                key = None
                names = sorted(os.listdir(matched), key=lambda x: x.lower())
                for name in names:
                    if name.startswith('%'):
                        
                        # See if we can use this item.
                        # ============================
                        # We want to allow file matches for the last URL path
                        # part, and in that case we strip the file extension. 
                        # For other matches we need them to be directories.

                        fs = join(matched, name)
                        k = name[1:]
                        v = part
                        if i == (nparts - 1):
                            if isfile(fs):
                                k = k.rsplit('.', 1)[0]
                                v = part.rsplit('.', 1)[0]
                        elif not isdir(fs):
                            continue 


                        # We found a suitable match at the current level.
                        # ===============================================

                        matched = fs 
                        key, value = _typecast(k, v)
                        request.path[key] = value
                        break # Only use the first %match per level.

                if key is None:
                    matched = request.root
                    break # no matched, reset
        if matched != request.root:
            request.fs = matched.rstrip(os.sep)

def _typecast(key, value):
    """Given two strings, return a string, and an int or string.
    """
    if key.endswith('.int'):    # you can typecast to int
        key = key[:-4]
        try:
            value = int(value)
        except ValueError:
            raise Response(404)
    else:                       # otherwise it's ASCII
        try:
            value = value.decode('ASCII')
        except UnicodeDecodeError:
            raise Response(400)
    return key, value

def trailing_slash(request):
    if isdir(request.fs):
        if not request.path.raw.endswith('/'):
            parts = list(request.urlparts)
            parts[2] += '/'
            location = urlparse.urlunparse(parts)
            raise Response(301, headers={'Location': location})

def index(request):
    if isdir(request.fs):
        index = join(request.fs, 'index.html')
        if isfile(index):
            request.fs = index

def autoindex(request, want_autoindex, autoindex):
    if isdir(request.fs):
        if want_autoindex:
            request.headers.set('X-Aspen-AutoIndexDir', request.fs)
            request.fs = autoindex 
            assert request.fs is not None # sanity check
        else:
            raise Response(404)

def socket_files(request):
    if 0 and '.sock/' in request.fs:
        parts = request.fs.split('.sock/')
        assert len(parts) == 2
        request.fs = parts[0] + '.sock'
        sockinfo = parts[1].split('/')
        ninfo = len(sockinfo)
        if ninfo >= 1:
            request.transport = sockinfo[0]
        if ninfo >= 2:
            request.session_id = sockinfo[1]
        if ninfo >= 3:
            pass # what is this?

def not_found(request, favicon):
    if not isfile(request.fs):
        if request.path.raw == '/favicon.ico': # special case
            request.fs = favicon
        else:
            raise Response(404)
