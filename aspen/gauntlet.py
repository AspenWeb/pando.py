"""Define a bunch of functions that change the request.

These functions determine the handelability of a request, and run in the order
given here.

"""
import os
import mimetypes
from os.path import basename, join, isfile, isdir, exists
try: # python2.6+
    from collections import namedtuple
except ImportError: # < python2.6
    from backcompat import namedtuple

from aspen import Response

def debug_noop(*args,**kwargs):
    pass

def debug_stdout(func):
    print "DEBUG: " + str(func())

debug=debug_noop

def splitext(name):
    parts = name.rsplit('.',1) + [None]
    return parts[:2]

def _typecast(key, value):
    """Given two strings, return a string, and an int or string.
    """
    debug( lambda: "typecasting " + key + ", " + value )
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
    debug( lambda: "typecasted " + key + ", " + repr(value) )
    return key, value

def strip_matching_ext(a, b):
    """given two names, strip a trailing extension iff they both have them"""
    aparts = splitext(a)
    bparts = splitext(b)
    debug_ext = lambda: "exts: " + str(a) + "( " + str(aparts[1]) + " ) and " + str(b) + "( " + str(bparts[1]) + " )"
    if aparts[1] == bparts[1]:
        debug( lambda: debug_ext() + " matches" )
        return aparts[0], bparts[0]
    debug( lambda: debug_ext() + " don't match" )
    return a, b

class DispatchStatus:
    okay, missing, non_leaf = range(3)

DispatchResult = namedtuple('DispatchResult', 'status match wildcards detail'.split()) 

def dispatch_abstract(listnodes, is_leaf, traverse, find_index, noext_matched, startnode, nodepath):
    """Given a list of nodenames (in 'nodepath'), tries to traverse the
       directed graph rooted at 'startnode' using the functions:
           listnodes(joinedpath) - which lists the nodes in the specified joined path
           is_leaf(node) - which returns true iff the specified node is a leaf node
           traverse(joinedpath, newnode) - which returns a new joined path by traversing into newnode from the current joinedpath
           find_index(joinedpath) - which returns the index file in the specified path if it exists, or None if not
           noext_matched(node) - is called iff node is matched with no extension instead of fully
       Wildcards nodenames start with %.  non-leaf wildcards are used askeys in wildvals and their actual path names are used as their values.
       In general, the rule for matching is 'most specific wins':
          $foo looks for isfile($foo) then isfile($foo-minus-extention) then isfile(virtual-with-extention) then isfile(virtual-no-extension) then isdir(virtual)
       Returns a DispatchResult, a namedtuple described above.
    """
    # TODO: noext_matched wildleafs are borken
    wildvals, wildleafs = {}, {}
    curnode = startnode
    is_wild = lambda n : n.startswith('%')
    lastnode_ext = splitext(nodepath[-1])[1]
    for depth, node in enumerate(nodepath):
        if not node:
            # empty path segment - only possible in the last position
            subnode = traverse(curnode, node)
            idx = find_index(subnode)
            if idx is None:
                # this makes the resulting path end in /, meaning autoindex or 404 as appropriate
                idx = ""
            curnode = traverse(subnode, idx)
            break
        subnodes = listnodes(curnode)
        subnodes.sort()
        node_noext, node_ext = splitext(node)
        # look for matches, and gather future options
        found_direct, found_indirect = None, None
        wildsubs = []
        for n in subnodes:
            if n.startswith('.'):
                # don't serve hidden files
                continue
            if node == n:
                # exact name match
                found_direct = n
                break
            n_is_leaf = is_leaf(traverse(curnode, n))
            if node_noext == n and n_is_leaf:
                # negotiated/indirect filename match - only for files
                found_indirect = n
                continue
            if not is_wild(n): continue
            if not n_is_leaf:
                debug( lambda: "not is_leaf " + n )
                wildsubs.append(n)
                continue
            # wild leafs are fallbacks if anything goes missing
            # though they still have to match extension
            ## figure out the wildcard value
            wildwildvals = wildvals.copy()
            remaining = reduce(traverse, nodepath[depth:])
            k, v = strip_matching_ext(n[1:], remaining)
            k, v = _typecast(k, v)
            wildwildvals[k] = v
            ## store it 
            n_ext = splitext(n)[1]
            wildleafs[n_ext] = (traverse(curnode, n), wildwildvals)
        if found_direct: 
            # exact match
            debug( lambda : "Exact match " + str(node))
            curnode = traverse(curnode, found_direct)
            continue
        if found_indirect:
            # matched but no extension
            debug( lambda : "Indirect match " + str(node))
            noext_matched(node)
            curnode = traverse(curnode, found_indirect)
            continue
        ## now look for wildcard matches
        wildleaf_fallback = lastnode_ext in wildleafs or None in wildleafs
        last_pathseg = depth == len(nodepath) - 1
        if wildleaf_fallback and (last_pathseg or not wildsubs):
            ext = lastnode_ext if lastnode_ext in wildleafs else None
            curnode, wildvals = wildleafs[ext]
            debug( lambda : "Wildcard leaf match " + str(curnode) + " because last_pathseg:" + str(last_pathseg) + " and ext " + str(ext))
            break
        if wildsubs:
            # wildcard subnode matches
            n = wildsubs[0]
            k, v = _typecast(n[1:], node)
            wildvals[k] = v
            curnode = traverse(curnode, n)
            debug( lambda : "Wildcard subnode match " + str(n))
            continue
        return DispatchResult(DispatchStatus.missing, None, None, "Node '" + str(node) +"' Not Found")
    else:
        debug( lambda: "else clause tripped; testing is_leaf " + str(curnode) )
        if not is_leaf(curnode):
            return DispatchResult(DispatchStatus.non_leaf, curnode, None, "Tried to access non-leaf node as leaf.")
    return DispatchResult(DispatchStatus.okay, curnode, wildvals, "Found.")

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

def match_index(request, indir):
    for filename in request.website.indices:
        index = join(indir, filename)
        if isfile(index):
            return index
    return None

def update_neg_type(request, filename):
    media_type = mimetypes.guess_type(filename, strict=False)[0]
    if media_type is None:
        media_type = self.website.media_type_default
    request.headers['X-Aspen-Accept'] = media_type


def dispatch(request, pure_dispatch=False):
    """This is the 'adapter' that applies dispatch_abstract(), above, to the 'real world'.
       It's all side-effecty on the request object, setting, at the least, request.fs, and at worst
       other random contents including but not limited to: request.line.uri.path, request.headers, 
    """

    # legacy (?) websocket handling
    intercept_socket(request)

    # set up the real environment for the dispatcher, then dispatch
    listnodes = os.listdir
    is_leaf = os.path.isfile
    traverse = os.path.join
    find_index = lambda x: match_index(request, x)
    noext_matched = lambda x: update_neg_type(request, x)
    startdir = request.website.www_root
    pathsegs = request.line.uri.path.decoded.lstrip('/').split('/')
    result = dispatch_abstract( listnodes, is_leaf, traverse, find_index, noext_matched, startdir, pathsegs )

    # provide a favicon if there's not one
    if not pure_dispatch and request.line.uri.path.raw == '/favicon.ico' and result.status != DispatchStatus.okay:
        request.fs = request.website.find_ours( request.line.uri.path.raw[1:] )
        return
    # don't let robots.txt be handled by anything other than an actual robots.txt file
    if not pure_dispatch and request.line.uri.path.raw == '/robots.txt':
        if result.status != DispatchStatus.missing and not result.match.endswith('robots.txt'):
            raise Response(404)

    # handle returned states
    if result.status == DispatchStatus.okay:
        # handle autoindex
        if result.match.endswith('/'):
            if not request.website.list_directories:
                raise Response(404)
            autoindex = request.website.ours_or_theirs('autoindex.html')
            assert autoindex is not None # sanity check
            request.headers['X-Aspen-AutoIndexDir'] = result.match
            request.fs = autoindex
            return # return so we skip the no-escape check
        # normal match
        request.fs = result.match
        for k, v in result.wildcards.iteritems():
            request.line.uri.path[k] = v
    elif result.status == DispatchStatus.non_leaf:
        # requested a dir without a trailing slash; redirect to the same but with a trailing slash
        uri = request.line.uri
        location = uri.path.raw + '/'
        if uri.querystring.raw:
            location += '?' + uri.querystring.raw
        raise Response(301, headers={'Location': location})
    elif result.status == DispatchStatus.missing:
        raise Response(404)
    else:
        raise "Unknown result status - internal error"
    # not allowed to escape the www_root
    if not request.fs.startswith(startdir):
        raise Response(404)

run = run_through = dispatch

