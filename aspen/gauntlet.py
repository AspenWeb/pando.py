"""Define a bunch of functions that change the request.

These functions determine the handelability of a request, and run in the order
given here.

"""
import os
from os.path import basename, join, isfile, isdir, exists

from aspen import Response


def intercept_socket(request):
    """Given a request object, return a tuple of (str, None) or (str, str).

    Intercept socket requests. We modify the filesystem path so that your
    application thinks the request was to /foo.sock instead of to
    /foo.sock/blah/blah/blah/.

    """
    path = request.line.uri.path.decoded
    if path.endswith('.sock'):
        # request.line.uri.path.raw does not include querystring.
        raise Response(404)
    parts = path.rsplit('.sock/', 1)
    if len(parts) == 1:
        path = parts[0]
        socket = None
    else:
        path = parts[0] + '.sock'
        socket = parts[1]
    request.line.uri.path.decoded, request.socket = path, socket

def translate(request):
    """Translate urlpath to fspath, returning urlpath parts.

    We specifically avoid removing symlinks in the path so that the filepath
    remains under the website root. Also, we don't want trailing slashes for
    directories in request.fs.

    """
    parts = [request.website.www_root]
    parts += request.line.uri.path.decoded.lstrip('/').split('/')
    request.fs = os.sep.join(parts).rstrip(os.sep)
    request._parts = parts # store for use in processing virtual_paths

def check_sanity(request):
    """Make sure the request is under our root.
    """
    if not request.fs.startswith(request.website.www_root):
        raise Response(404)

def hidden_files(request):
    """Protect hidden files.
    """
    if '/.' in request.fs[len(request.website.www_root):]:
        raise Response(404)

def indirect_negotiation(request):
    """Requests for /foo.html should be servable by /foo.

    Negotiate resources are those that have no file extension. One way to
    multiplex requests onto a single such file is to use the Accept request
    header to specify a media type preference. This method implements support
    for indexing into negotiated resources using the file extension in the URL
    path as well. Note that this only works if there is exactly one dot (.) in
    the URL, as otherwise direct requests for the same resource would get
    convoluted.

    """
    if not isfile(request.fs):
        path = request.fs.rsplit('.', 1)[0]
        filename = basename(path)
        if '.' not in filename:
            if isfile(path):
                media_type = request._infer_media_type()
                request.headers['X-Aspen-Accept'] = media_type
                # We look for X-Aspen-Accept before Accept.
                # "The default value is q=1."
                #   http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
                # That means that setting to 'text/html' will enforce only
                # that one media type and fail if it's not available.
                request.fs = path

def virtual_paths(request):
    """Support /foo/bar.html => ./%blah/bar.html and /blah.html => ./%flah.html

    Parts is a list of fs path parts as returned by translate, above.

    Path parts will end up in request.line.uri.path, a Mapping. There can
    only be one variable per path part. If a directory has more than one
    subdirectory starting with '%' then only the 'first' is used.

    """
    if os.sep + '%' in request.fs[len(request.website.www_root):]:
        raise Response(404)     # disallow direct access

    if request.line.uri.path.raw in ('/favicon.ico', '/robots.txt'):
        # Special case. Aspen bundles its own favicon.ico, and it wants to
        # serve that if it can rather then letting it fall through to a virtual
        # path. For robots.txt we just want to avoid spam in a common case.
        return

    if exists(request.fs):
        # Exit early. The file exists as requested, so don't go looking for a
        # virtual path.
        return

    matched = request.website.www_root
    parts = request._parts
    del request._parts

    def _match_remaining(rparts, matched):
        """given
               rparts - unmatched request parts
               matched - fs path matched so far
           return the matched file to dispatch to
        """
        part = rparts[0]
        part_noext = part.split('.', 1)[0]
        next = join(matched, part)
        next_noext = join(matched, part_noext)
        root, dirs, files = os.walk(matched).next()
        files.sort(key=lambda x: x.lower())
        dirs.sort(key=lambda x: x.lower())

        if len(rparts) > 1:
            # looking for a dir, or if not found, a greedy simplate
            ## if this matches it's a real dir
            if exists(next):
                return _match_remaining(rparts[1:], next)

            ## if this matches, it's a virtual dir, so recurse
            for name in dirs:
                if name.startswith('%'):
                    key, value = _typecast(name[1:], part)
                    request.line.uri.path[key] = value
                    recurse = _match_remaining(rparts[1:], join(matched, name))
                    if recurse is not None:
                        return recurse

            ## if this matches, it's a greedy simplate; the value is the full path
            fullparts = '/'.join(rparts)
            for name in files:
                if name.startswith('%') and _ext_matches_if_present(rparts[-1], name):
                    k = name.rsplit('.',1)[0][1:]
                    lastpart_noext = rparts[-1].rsplit('.', 1)[0]
                    fullparts_noext = '/'.join(rparts[:-1] + [lastpart_noext])
                    v = fullparts_noext
                    key, value = _typecast(k, v)
                    request.line.uri.path[key] = value
                    return join(matched, name)

        else:
            # check for immediate match
            if exists(next):
                return next

            # indirect negotiation
            if exists(next_noext) and not isdir(next_noext):
                request.headers['X-Aspen-Accept'] = request._infer_media_type()
                return next_noext

            # looking for a final dir, if it contains an index path
            for name in dirs:
                if name.startswith('%'):
                    p = match_index(request, join(matched, name))
                    if p is not None and _ext_matches_if_present(part, basename(p)):
                        key, value = _typecast(name[1:], part)
                        request.line.uri.path[key] = value
                        return join(matched, name)

            # no dir matched, look for a virtual file that might
            for name in files:
                if name.startswith('%') and _ext_matches_if_present(part, name):
                    k = name.rsplit('.',1)[0][1:]
                    v = '/'.join(rparts).rsplit('.',1)[0]
                    key, value = _typecast(k, v)
                    request.line.uri.path[key] = value
                    return join(matched, name)

        # not found
        return None

    request.fs = _match_remaining(parts, matched) or request.fs

def _ext_matches_if_present(r, f):
    """return true if either both have a matching extension, or r
       has one and f doesn't"""
    r_parts = r.rsplit('.',1) + [ None ]
    f_parts = f.rsplit('.',1) + [ None ]
    return (len(r_parts) < 4) and (r_parts[1] == f_parts[1]) or (f_parts[1] == None) or (r_parts[0] == f)

def _typecast(key, value):
    """Given two strings, return a string, and an int or string.
    """
    if key.endswith('.int'):    # you can typecast to int
        key = key[:-4]
        try:
            value = int(value)
        except ValueError:
            raise Response(404)
    else:                       # otherwise it's URL-quoted ASCII
        try:
            value = value.decode('ASCII')
        except UnicodeDecodeError:
            raise Response(400)
    return key, value

def trailing_slash(request):
    if isdir(request.fs):
        uri = request.line.uri
        if not uri.path.raw.endswith('/'):
            uri.path.raw += '/'
            location = uri.path.raw
            if uri.querystring.raw:
                location += '?' + uri.querystring.raw
            raise Response(301, headers={'Location': location})

def index(request):
    if isdir(request.fs):
        for filename in request.website.indices:
            index = join(request.fs, filename)
            if isfile(index):
                request.fs = index
                break

def match_index(request, indir):
    for filename in request.website.indices:
        index = join(indir, filename)
        if isfile(index):
            return index
    return None


def autoindex(request):
    if isdir(request.fs):
        if request.website.list_directories:
            request.headers['X-Aspen-AutoIndexDir'] = request.fs
            request.fs = request.website.ours_or_theirs('autoindex.html')
            assert request.fs is not None # sanity check
        else:
            raise Response(404)

def not_found(request):
    if not isfile(request.fs):
        if request.line.uri.path.raw == '/favicon.ico': # special case
            request.fs = request.website.find_ours('favicon.ico')
        else:
            raise Response(404)


gauntlet = [ intercept_socket
           , translate
           , check_sanity
           , hidden_files
           , indirect_negotiation
           , virtual_paths
           , trailing_slash
           , index
           , autoindex
           , not_found
            ]

def run(request):
    """Given a request, run it through the gauntlet.
    """
    for func in gauntlet:
        func(request)

def run_through(request, last):
    """For testing, here's a function that runs part of the gauntlet.

    Pass in a request object and a gauntlet function, the last to be run.

    """
    for func in gauntlet:
        func(request)
        if func is last:
            break
