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
    """Support /foo/bar.html => ./%blah/bar.html

    Path parts will end up in request.path, a dict subclass. There can only be 
    one variable per path part. If a directory has more than one subdirectory
    starting with '%' then only the first as sorted by os.listdir is used.

    """
    if '/%' in request.fs[len(request.root):]:  # disallow direct access
        raise Response(404)
    if not exists(request.fs):
        candidate = request.root
        for part in parts[1:]:
            next = join(candidate, part)
            if exists(next):    # this URL part names an actual directory
                candidate = next
            else:               # this part is missing; do we have a %subdir?
                key = None
                subdirs = sorted(os.listdir(candidate), key=lambda x: x.lower())
                for subdir in subdirs:
                    if subdir.startswith('%'):
                        key = subdir[1:]
                        if key.endswith('.int'):    # you can typecast to int
                            key = key[:-4]
                            try:
                                part = int(part)
                            except ValueError:
                                raise Response(404)
                        else:                       # otherwise it's ASCII
                            try:
                                part = part.decode('ASCII')
                            except UnicodeDecodeError:
                                raise Response(400)
                        candidate = join(candidate, subdir)
                        request.path[key] = part
                        break   # only use first %subdir per dir
                if key is None:
                    break # not candidate
        if candidate != request.root:
            request.fs = candidate.rstrip(os.sep)

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
