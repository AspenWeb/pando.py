"""Aspen uses Resource classes to model HTTP resources.

Here is the class hierarchy:

    Resource ------> DynamicResource ------> JSONResource
             \                       \ 
              \                       \----> SocketResource
               \                       \
                \--> StaticResource     \--> TemplateResource

XXX: There is lots of semantic ambiguity and overlap between Resource and
Simplate.

"""
import datetime
import logging
import mimetypes
import os
import stat
import sys
import traceback
from os.path import join

PAGE_BREAK = chr(12) # used in the following imports

from aspen import json
from aspen.resources.json_resource import JSONResource
from aspen.resources.template_resource import TemplateResource
from aspen.resources.socket_resource import SocketResource
from aspen.resources.static_resource import StaticResource


log = logging.getLogger('aspen.resources')


class LoadError(StandardError):
    """Represent a problem loading a resource.
    """


# Cache helpers
# =============

__cache__ = dict()        # cache, keyed to filesystem path

class Entry:
    """An entry in the global resource cache.
    """

    fspath = ''         # The filesystem path [string]
    modtime = None      # The timestamp of the last change [int]
    quadruple = None    # A post-processed version of the data [4-tuple]
    exc = None          # Any exception in reading or compilation [Exception]

    def __init__(self):
        self.fspath = ''
        self.modtime = 0
        self.quadruple = ()


# Core loaders
# ============

def get_resource_class(raw, mimetype):
    """Given raw file contents and a mimetype, return a Resource subclass.

    This function encodes the algorithm for deciding what kind of Resource (==
    simplate) a given file is. Is it a static file or a dynamic JSON simplate
    or what? Etc. Here is the algorithm:

        If mimetype is 'application/x-socket.io' then it's a Socket simplate.

        If mimetype is 'text/*' or 'application/json' then we look for page
        breaks (^L). If there aren't any page breaks then it's a static file.
        If it has at least one page break then it's a dynamic simplate (either
        Template or JSON).

        For all other mimetypes we sniff the first few bytes of the file. If it
        looks Python-y then it's a Template simplate, otherwise it's a static
        file. What looks Python-y? Triple quotes for a leading docstring, or
        the beginning of an import statement ("from" or "import").
    
    """

    is_dynamic = True

    if mimetype == 'application/x-socket.io':
        
        # *.sock files are always dynamic.

        pass

    elif mimetype.startswith('text/') or mimetype == 'application/json':

        # For text formats we can perform a highly accurate test for
        # dynamicity.

        c = lambda s: s in raw
        is_dynamic = c("") or c("^L")

    else:

        # For binary formats we must rely on a less-accurate test. This is
        # because a binary file can have s in it without being a resource--
        # and I've actually seen, in the wild, a file with exactly two s. So
        # we sniff the first few bytes.

        s = lambda s: raw.startswith(s)
        is_dynamic = s('"""') or s('import') or s('from')

    if not is_dynamic:
        Class = StaticResource
    elif mimetype == 'application/json':
        Class = JSONResource
    elif mimetype == 'application/x-socket.io':
        Class = SocketResource
    else:
        Class = TemplateResource

    return Class


def load(request, modtime):
    """Given a Request and a modtime, return a Resource object (w/o caching).
    """

    # Load bytes.
    # ===========
    # We work with resources exclusively as bytestrings. Any unicode objects
    # passed in by the user as {{ expressions }} in Resources will be encoded
    # with UTF-8 by Tornado.

    raw = open(request.fs, 'rb').read()
    
   
    # Compute a mimetype.
    # ===================

    mimetype = mimetypes.guess_type(request.fs, strict=False)[0]
    if mimetype is None:
        mimetype = request.default_mimetype


    # Compute and instantiate a class.
    # ================================
    # An instantiated resource is compiled as far as we can take it.
 
    Class = get_resource_class(raw, mimetype)
    resource = Class(request.website, request.fs, raw, mimetype, modtime)
    return resource


def get(request):
    """Given a Request, return a Resource object (with caching).

    We need the request because it carries default_mimetype.

    """

    # XXX This is not thread-safe. It used to be, but then I simplified it
    # when I switched to diesel. Now that we have multiple engines, some of
    # which are threaded, we need to make this thread-safe again.
    
    # Get a cache Entry object.
    # =========================

    if request.fs not in __cache__:
        entry = Entry()
        __cache__[request.fs] = entry

    entry = __cache__[request.fs]


    # Process the resource.
    # =====================

    modtime = os.stat(request.fs)[stat.ST_MTIME]
    if entry.modtime == modtime:                            # cache hit
        if entry.exc is not None:
            raise entry.exc
    else:                                                   # cache miss
        try:
            entry.resource = load(request, modtime)
        except:     # capture any Exception
            entry.exc = ( LoadError(traceback.format_exc())
                        , sys.exc_info()[2]
                         )
        else:       # reset any previous Exception
            entry.exc = None 

        entry.modtime = modtime
        if entry.exc is not None:
            raise entry.exc[0] # TODO Why [0] here, and not above?


    # Return
    # ======
    # The caller must take care to avoid mutating any namespace dictionary at 
    # entry.resource.pages[0].

    return entry.resource
