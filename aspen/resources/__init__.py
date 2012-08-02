"""Aspen uses resources to model HTTP resources.

Here is the class hierarchy:

    Resource                            Logic Pages     Content Pages
     +-- DynamicResource                -----------------------------
     |    +-- JSONResource                  1 or 2          0
     |    +-- NegotiatedResource            2               1 or more
     |    |    +-- RenderedResource         1 or 2          1
     |    +-- SocketResource                1, 2, or 3      0
     +-- StaticResource                     0               1


The call chain looks like this for static resources:

    StaticResource.respond(request, response)


It's more complicate for dynamic resources:

    DynamicResource.respond
        DynamicResource.parse



"""
import mimetypes
import os
import stat
import sys
import traceback

PAGE_BREAK = chr(12) # used in the following imports

from aspen.exceptions import LoadError
from aspen.resources.json_resource import JSONResource
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.resources.rendered_resource import RenderedResource
from aspen.resources.socket_resource import SocketResource
from aspen.resources.static_resource import StaticResource


# Cache helpers
# =============

__cache__ = dict()        # cache, keyed to filesystem path

class Entry:
    """An entry in the global resource cache.
    """

    fspath = ''         # The filesystem path [string]
    mtime = None        # The timestamp of the last change [int]
    quadruple = None    # A post-processed version of the data [4-tuple]
    exc = None          # Any exception in reading or compilation [Exception]

    def __init__(self):
        self.fspath = ''
        self.mtime = 0
        self.quadruple = ()


# Core loaders
# ============

def get_resource_class(filename, raw, media_type):
    """Given raw file contents and a media type, return a Resource subclass.

    This function encodes the algorithm for deciding what kind of Resource a
    given file is. Is it a static file or a dynamic JSON resource or what? Etc.
    The first step is to decide whether it's static or dynamic:

        If media type is 'application/x-socket.io' then we know it's dynamic.

        If media type is 'text/*' or 'application/json' then we look for page
        breaks (^L). If there aren't any page breaks then it's a static file.
        If it has at least one page break then it's a dynamic resource.

        For all other media types we sniff the first few bytes of the file. If
        it looks Python-y then it's dynamic, otherwise it's a static file. What
        looks Python-y? Triple quotes for a leading docstring, or the beginning
        of an import statement ("from" or "import").

    Step two is to decide what kind of dynamic resource it is. JSON and Socket
    are based on media type. Otherwise it's Rendered if there is a file
    extension and Negotiated if not.

    """

    # XXX What is media_type coming in for a negotiated resource? Is it None?
    # application/octet-stream? text/plain? Are we going to look for ^L or
    # sniff the first few bytes? The answer is media_type_default. See .load.

    is_dynamic = True

    if media_type == 'application/x-socket.io':

        # *.sock files are always dynamic.

        pass

    elif media_type.startswith('text/') or media_type == 'application/json':

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
    elif media_type == 'application/json':
        Class = JSONResource
    elif media_type == 'application/x-socket.io':
        Class = SocketResource
    elif '.' in os.path.basename(filename):
        Class = RenderedResource
    else:
        Class = NegotiatedResource

    return Class


def load(request, mtime):
    """Given a Request and a mtime, return a Resource object (w/o caching).
    """

    # Load bytes.
    # ===========
    # We work with resources exclusively as bytestrings. Renderers take note.

    raw = open(request.fs, 'rb').read()


    # Compute a media type.
    # =====================
    # For a negotiated resource we will ignore this.

    media_type = mimetypes.guess_type(request.fs, strict=False)[0]
    if media_type is None:
        media_type = request.website.media_type_default


    # Compute and instantiate a class.
    # ================================
    # An instantiated resource is compiled as far as we can take it.

    Class = get_resource_class(request.fs, raw, media_type)
    resource = Class(request.website, request.fs, raw, media_type, mtime)
    return resource


def get(request):
    """Given a Request, return a Resource object (with caching).

    We need the request because it carries media_type_default.

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

    mtime = os.stat(request.fs)[stat.ST_MTIME]
    if entry.mtime == mtime:                                # cache hit
        if entry.exc is not None:
            raise entry.exc
    else:                                                   # cache miss
        try:
            entry.resource = load(request, mtime)
        except:     # capture any Exception
            entry.exc = ( LoadError(traceback.format_exc())
                        , sys.exc_info()[2]
                         )
        else:       # reset any previous Exception
            entry.exc = None

        entry.mtime = mtime
        if entry.exc is not None:
            raise entry.exc[0] # TODO Why [0] here, and not above?


    # Return
    # ======
    # The caller must take care to avoid mutating any context dictionary at
    # entry.resource.pages[0].

    return entry.resource
