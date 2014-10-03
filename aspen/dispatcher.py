"""
aspen.dispatcher
++++++++++++++++

Implement Aspen's filesystem dispatch algorithm.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mimetypes
import os

from aspen import Response


def debug_noop(*args, **kwargs):
    pass


def debug_stdout(func):
    r = func()
    try:
        print("DEBUG: " + r)
    except Exception:
        print("DEBUG: " + repr(r))

debug = debug_stdout if 'ASPEN_DEBUG' in os.environ else debug_noop


def splitext(name):
    parts = name.rsplit('.', 1) + [None]
    return parts[:2]


def strip_matching_ext(a, b):
    """Given two names, strip a trailing extension iff they both have them.
    """
    aparts = splitext(a)
    bparts = splitext(b)

    def debug_ext():
        return "exts: %r( %r ) and %r( %r )" % (a, aparts[1], b, bparts[1])

    if aparts[1] == bparts[1]:
        debug(lambda: debug_ext() + " matches")
        return aparts[0], bparts[0]
    debug(lambda: debug_ext() + " don't match")
    return a, b


class DispatchStatus(object):
    okay, missing, non_leaf = range(3)


class DispatchResult(object):
    def __init__(self, status, match, wildcards, detail, extra):
        self.status = status
        self.match = match
        self.wildcards = wildcards
        self.detail = detail
        self.extra = extra


def dispatch_abstract(listnodes, is_leaf, traverse, find_index, noext_matched,
                      startnode, nodepath):
    """Given a list of nodenames (in 'nodepath'), return a DispatchResult.

    We try to traverse the directed graph rooted at 'startnode' using the
    functions:

       listnodes(joinedpath) - lists the nodes in the specified joined path

       is_leaf(node) - returns true iff the specified node is a leaf node

       traverse(joinedpath, newnode) - returns a new joined path by traversing
        into newnode from the current joinedpath

       find_index(joinedpath) - returns the index file in the specified path if
        it exists, or None if not

       noext_matched(node) - is called iff node is matched with no extension
        instead of fully

    Wildcards nodenames start with %. Non-leaf wildcards are used as keys in
    wildvals and their actual path names are used as their values. In general,
    the rule for matching is 'most specific wins': $foo looks for isfile($foo)
    then isfile($foo-minus-extension) then isfile(virtual-with-extension) then
    isfile(virtual-no-extension) then isdir(virtual)

    """
    # TODO: noext_matched wildleafs are borken
    wildvals, wildleafs = {}, {}
    curnode = startnode
    is_spt = lambda n: n.endswith(".spt")
    is_leaf_node = lambda n: is_leaf(traverse(curnode, n))
    lastnode_ext = splitext(nodepath[-1])[1]

    def get_wildleaf_fallback():
        wildleaf_fallback = lastnode_ext in wildleafs or None in wildleafs
        if wildleaf_fallback:
            ext = lastnode_ext if lastnode_ext in wildleafs else None
            curnode, wildvals = wildleafs[ext]
            debug(lambda: "Wildcard leaf match %r and ext %r" % (curnode, ext))
            return DispatchResult(DispatchStatus.okay, curnode, wildvals, "Found.", {})
        return None

    for depth, node in enumerate(nodepath):

        # check all the possibilities:
        # node.html, node.html.spt, node.spt, node.html/, %node.html/ %*.html.spt, %*.spt

        # don't serve hidden files
        subnodes = set([ n for n in listnodes(curnode) if not n.startswith('.') ])

        node_noext, node_ext = splitext(node)

        # only maybe because non-spt files aren't wild
        maybe_wild_nodes = [ n for n in sorted(subnodes) if n.startswith("%") ]

        wild_leaf_ns = [ n for n in maybe_wild_nodes if is_leaf_node(n) and is_spt(n) ]
        wild_nonleaf_ns = [ n for n in maybe_wild_nodes if not is_leaf_node(n) ]

        # store all the fallback possibilities
        remaining = reduce(traverse, nodepath[depth:])
        for n in wild_leaf_ns:
            wildwildvals = wildvals.copy()
            k, v = strip_matching_ext(n[1:-4], remaining)
            wildwildvals[k] = v
            n_ext = splitext(n[:-4])[1]
            wildleafs[n_ext] = (traverse(curnode, n), wildwildvals)

        debug(lambda: "wildleafs is %r" % wildleafs)

        found_n = None
        last_node = (depth + 1) == len(nodepath)
        if last_node:
            debug(lambda: "on last node %r" % node)
            if node == '':  # dir request
                debug(lambda: "...last node is empty")
                path_so_far = traverse(curnode, node)
                # return either an index file or have the path end in '/' which means 404 or
                # autoindex as appropriate
                found_n = find_index(path_so_far)
                if found_n is None:
                    found_n = ""
                    if wild_leaf_ns:
                        found_n = wild_leaf_ns[0]
                        curnode = traverse(curnode, found_n)
                        node_name = found_n[1:-4]  # strip leading % and trailing .spt
                        wildvals[node_name] = node
                        return DispatchResult(DispatchStatus.okay, curnode, wildvals, "Found.", {})
            elif node in subnodes and is_leaf_node(node):
                debug(lambda: "...found exact file, must be static")
                if is_spt(node):
                    return DispatchResult( DispatchStatus.missing
                                         , None
                                         , None
                                         , "Node %r Not Found" % node
                                         , {}
                                          )
                else:
                    found_n = node
            elif node + ".spt" in subnodes and is_leaf_node(node + ".spt"):
                debug(lambda: "...found exact spt")
                found_n = node + ".spt"
            elif node_noext + ".spt" in subnodes and is_leaf_node(node_noext + ".spt") \
                    and node_ext:
                # node has an extension
                debug(lambda: "...found indirect spt")
                # indirect match
                noext_matched(node)
                found_n = node_noext + ".spt"

            if found_n is not None:
                debug(lambda: "found_n: %r" % found_n)
                curnode = traverse(curnode, found_n)
            elif wild_nonleaf_ns:
                debug(lambda: "wild_nonleaf_ns")
                found_n = wild_nonleaf_ns[0]
                curnode = traverse(curnode, found_n)
                result = get_wildleaf_fallback()
                if not result:
                    return DispatchResult( DispatchStatus.non_leaf
                                         , curnode
                                         , None
                                         , "Tried to access non-leaf node as leaf."
                                         , {}
                                          )
                return result
            elif node in subnodes:
                debug(lambda: "exact dirmatch")
                return DispatchResult( DispatchStatus.non_leaf
                                     , curnode
                                     , None
                                     , "Tried to access non-leaf node as leaf."
                                     , {}
                                      )
            else:
                debug(lambda: "fallthrough")
                result = get_wildleaf_fallback()
                if not result:
                    return DispatchResult( DispatchStatus.missing
                                         , None
                                         , None
                                         , "Node %r Not Found" % node
                                         , {}
                                          )
                return result

        if not last_node:  # not at last path seg in request
            debug(lambda: "on node %r" % node)
            if node in subnodes and not is_leaf_node(node):
                found_n = node
                debug(lambda: "Exact match " + repr(node))
                curnode = traverse(curnode, found_n)
            elif wild_nonleaf_ns:
                # need to match a wildnode, and we're not the last node, so we should match
                # non-leaf first, then leaf
                found_n = wild_nonleaf_ns[0]
                wildvals[found_n[1:]] = node
                debug(lambda: "Wildcard match %r = %r " % (found_n, node))
                curnode = traverse(curnode, found_n)
            else:
                debug(lambda: "No exact match for " + repr(node))
                result = get_wildleaf_fallback()
                if not result:
                    return DispatchResult( DispatchStatus.missing
                                         , None
                                         , None
                                         , "Node %r Not Found" % node
                                         , {}
                                          )
                return result

    return DispatchResult(DispatchStatus.okay, curnode, wildvals, "Found.", {})


def match_index(indices, indir):
    """return the full path of the first index in indir, or None if not found"""
    for filename in indices:
        index = os.path.join(indir, filename)
        if os.path.isfile(index):
            return index
    return None


def is_first_index(indices, basedir, name):
    """is the supplied name the first existing index in the basedir ?"""
    for i in indices:
        if i == name:
            return True
        if os.path.isfile(os.path.join(basedir, i)):
            return False
    return False


def update_neg_type(media_type_default, capture_accept, filename):
    media_type = mimetypes.guess_type(filename, strict=False)[0]
    if media_type is None:
        media_type = media_type_default
    capture_accept['accept'] = media_type
    debug(lambda: "set result.extra['accept'] to %r" % media_type)


def dispatch(website, indices, media_type_default, pathparts, uripath, querystring,
        pure_dispatch=False):
    """Concretize dispatch_abstract.
    """

    # Set up the real environment for the dispatcher.
    # ===============================================

    capture_accept = {}
    listnodes = os.listdir
    is_leaf = os.path.isfile
    traverse = os.path.join
    find_index = lambda x: match_index(indices, x)
    noext_matched = lambda x: update_neg_type(media_type_default, capture_accept, x)
    startdir = website.www_root


    # Dispatch!
    # =========

    result = dispatch_abstract( listnodes
                              , is_leaf
                              , traverse
                              , find_index
                              , noext_matched
                              , startdir
                              , pathparts
                               )

    debug(lambda: "dispatch_abstract returned: " + repr(result))

    if 'accept' in capture_accept:
        result.extra['accept'] = capture_accept['accept']

    if result.match:
        debug(lambda: "result.match is true" )
        matchbase, matchname = result.match.rsplit(os.path.sep,1)
        if pathparts[-1] != '' and matchname in indices and \
                is_first_index(indices, matchbase, matchname):
            # asked for something that maps to a default index file; redirect to / per issue #175
            debug( lambda: "found default index '%s' maps into %r"
                 % (pathparts[-1], indices)
                  )
            location = uripath[:-len(pathparts[-1])]
            if querystring:
                location += '?' + querystring
            raise Response(302, headers={'Location': location})

    if not pure_dispatch:

        # favicon.ico
        # ===========
        # Serve Aspen's favicon if there's not one.

        if uripath == '/favicon.ico':
            if result.status != DispatchStatus.okay:
                result.status = DispatchStatus.okay
                result.match = website.find_ours('favicon.ico')
                result.wildcards = {}
                result.detail = 'Found.'
                return result


        # robots.txt
        # ==========
        # Don't let robots.txt be handled by anything other than an actual
        # robots.txt file

        if uripath == '/robots.txt':
            if result.status != DispatchStatus.missing:
                if not result.match.endswith('robots.txt'):
                    raise Response(404)


    # Handle returned states.
    # =======================

    if result.status == DispatchStatus.okay:
        if result.match.endswith('/'):              # autoindex
            if not website.list_directories:
                raise Response(404)
            result.extra['autoindexdir'] = result.match
            result.match = website.ours_or_theirs('autoindex.html.spt')
            assert result.match is not None # sanity check
            return result  # return so we skip the no-escape check

    elif result.status == DispatchStatus.non_leaf:  # trailing-slash redirect
        location = uripath + '/'
        if querystring:
            location += '?' + querystring
        raise Response(302, headers={'Location': location})

    elif result.status == DispatchStatus.missing:   # 404
        raise Response(404)

    else:
        raise Response(500, "Unknown result status.")


    # Protect against escaping the www_root.
    # ======================================

    if not result.match.startswith(startdir):
        raise Response(404)

    return result
