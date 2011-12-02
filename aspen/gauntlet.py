"""Define a bunch of functions that change the request.

These functions determine the handelability of a request, and run in the order
given here.

"""
import logging
import os
import urlparse
from os.path import join, isfile, isdir, dirname, exists

from aspen import Response


log = logging.getLogger('aspen.gauntlet')


def intercept_socket(request):
    """Given a request object, return a tuple of (str, None) or (str, str).

    Intercept socket requests. We modify the filesystem path so that your
    application thinks the request was to /foo.sock instead of to
    /foo.sock/blah/blah/blah/.

    """
    if request.path.raw.endswith('.sock'):
        # request.path.raw does not include querystring.
        raise Response(404)
    parts = request.path.raw.rsplit('.sock/', 1)
    if len(parts) == 1:
        path = parts[0]
        socket = None
    else:
        path = parts[0] + '.sock'
        socket = parts[1]
    request.path.raw, request.socket = path, socket
    #spam -- log.debug('gauntlet.intercept_socket: ' + request.path.raw)

def translate(request):
    """Translate urlpath to fspath, returning urlpath parts.

    We specifically avoid removing symlinks in the path so that the filepath
    remains under the website root. Also, we don't want trailing slashes for
    directories in request.fs.

    """
    parts = [request.root] + request.path.raw.lstrip('/').split('/')
    request.fs = os.sep.join(parts).rstrip(os.sep)
    request._parts = parts # store for use in processing virtual_paths
    #spam -- log.debug('gauntlet.translate: ' + request.fs)

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

def virtual_paths(request):
    """Support /foo/bar.html => ./%blah/bar.html and /blah.html => ./%flah.html

    Parts is a list of fs path parts as returned by translate, above. 

    Path parts will end up in request.path, a dict subclass. There can only be 
    one variable per path part. If a directory has more than one subdirectory
    starting with '%' then only the 'first' is used.

    """
    if os.sep + '%' in request.fs[len(request.root):]:  # disallow direct access
        raise Response(404)
    if not exists(request.fs):
        matched = request.root
        parts = request._parts
        del request._parts
        nparts = len(parts)
        for i in range(1, nparts):
            part = parts[i]
            next = join(matched, part)
            if exists(next):    # this URL part names an actual directory
                matched = next
            else:               # this part is missing; do we have a %subdir?
                key = None
                for root, dirs, files in os.walk(matched):
                    files.sort(key=lambda x: x.lower())
                    dirs.sort(key=lambda x: x.lower())
                    for name in files + dirs:
                        if name.startswith('%'):
                            
                            # See if we can use this item.
                            # ============================
                            # We want to allow file matches for the last URL
                            # path part, and in that case we strip the file
                            # extension. For other matches we need them to be
                            # directories.

                            fs = join(matched, name)
                            k = name[1:]
                            v = part
                            if i == (nparts - 1):
                                if isfile(fs):
                                    # Take care with extensions.
                                    x = k.rsplit('.', 1)
                                    y = part.rsplit('.', 1)
                                    nx = len(x) # 1|2
                                    if nx != len(y):
                                        continue
                                    if nx == 2:
                                        # If there's an extension, match it.
                                        k, ext1 = x
                                        v, ext2 = y
                                        if ext1 != ext2:
                                            continue
                            elif not isdir(fs):
                                continue 


                            # We found a suitable match at the current level.
                            # ===============================================

                            matched = fs 
                            key, value = _typecast(k, v)
                            request.path[key] = value
                            break # Only use the first %match per level.
                    break # don't recurse in os.walk
                if key is None:
                    matched = request.root
                    break # no match, reset
        if matched != request.root:
            request.fs = matched.rstrip(os.sep)
    #spam -- log.debug('gauntlet.virtual_paths: ' + request.fs)

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
            request.path.raw += '/'
            raise Response(301, headers={'Location': request.rebuild_url()})

def index(request):
    if isdir(request.fs):
        for filename in request.default_filenames:
            index = join(request.fs, filename)
            if isfile(index):
                request.fs = index
                break
    #spam -- log.debug('gauntlet.index: ' + request.fs)

def autoindex(request):
    if isdir(request.fs):
        if request.conf.aspen.no('list_directories'):
            request.headers.set('X-Aspen-AutoIndexDir', request.fs)
            request.fs = request.website.ours_or_theirs('autoindex.html')
            assert request.fs is not None # sanity check
        else:
            raise Response(404)
    #spam -- log.debug('gauntlet.autoindex: ' + request.fs)

def not_found(request):
    if not isfile(request.fs):
        if request.path.raw == '/favicon.ico': # special case
            request.fs = request.website.find_ours('favicon.ico')
        else:
            raise Response(404)
    #spam -- log.debug('gauntlet.not_found: ' + request.fs)


gauntlet = [ intercept_socket
           , translate
           , check_sanity
           , hidden_files
           , virtual_paths
           , trailing_slash
           , index
           , autoindex
           , not_found
            ]

def run(request):
    """Given a request, run it through the gauntlet.
    """
    #spam -- log.debug('gauntlet.run: ' + request.path.raw)
    for func in gauntlet:
        func(request)

def run_through(request, last):
    """For testing, here's a function that runs part of the gauntlet.

    Pass in a request object and a gauntlet function, the last to be run.

    """
    #spam -- log.debug('gauntlet.run_through: ' + request.path.raw)
    for func in gauntlet:
        func(request)
        if func is last:
            break
