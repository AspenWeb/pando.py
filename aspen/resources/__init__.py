"""
aspen.resources
+++++++++++++++

Aspen uses resources to model HTTP resources.

Here is the class hierarchy:

    Resource                            Logic Pages     Content Pages
     +-- DynamicResource                -----------------------------
     |    +-- NegotiatedResource            2               1 or more
     |    |    +-- RenderedResource         1 or 2          1
     +-- StaticResource                     0               1


The call chain looks like this for static resources:

    StaticResource.respond(request, response)


It's more complicate for dynamic resources:

    DynamicResource.respond
        DynamicResource.parse



"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mimetypes
import os
import stat
import sys
import traceback

from aspen.exceptions import LoadError
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.resources.rendered_resource import RenderedResource
from aspen.resources.static_resource import StaticResource

# Cache helpers
# =============

__cache__ = dict()  # cache, keyed to filesystem path

class Entry:
    """An entry in the global resource cache.
    """

    fspath = ''  # The filesystem path [string]
    mtime = None  # The timestamp of the last change [int]
    quadruple = None  # A post-processed version of the data [4-tuple]
    exc = None  # Any exception in reading or compilation [Exception]

    def __init__(self):
        self.fspath = ''
        self.mtime = 0
        self.quadruple = ()


# Core loaders
# ============

def load(request, mtime):
    """Given a Request and a mtime, return a Resource object (w/o caching).
    """

    # Load bytes.
    # ===========
    # We work with resources exclusively as bytestrings. Renderers take note.

    raw_fh = open(request.fs, 'rb')
    raw = raw_fh.read()
    raw_fh.close() # explicit is better than implicit

    # Compute a media type.
    # =====================
    # For a negotiated resource we will ignore this.

    guess_with = request.fs
    is_spt = request.fs.endswith('.spt')
    if is_spt:
        guess_with = guess_with[:-4]
    media_type = mimetypes.guess_type(guess_with, strict=False)[0]
    if media_type is None:
        media_type = request.website.media_type_default


    # Compute and instantiate a class.
    # ================================
    # An instantiated resource is compiled as far as we can take it.

    if not is_spt:                                  # static
        Class = StaticResource
    elif '.' in os.path.basename(guess_with):       # rendered
        Class = RenderedResource
    else:                                           # negotiated
        Class = NegotiatedResource

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
    if entry.mtime == mtime:  # cache hit
        if entry.exc is not None:
            raise entry.exc
    else:  # cache miss
        try:
            entry.resource = load(request, mtime)
        except:  # capture any Exception
            entry.exc = (LoadError(traceback.format_exc())
                        , sys.exc_info()[2]
                         )
        else:  # reset any previous Exception
            entry.exc = None

        entry.mtime = mtime
        if entry.exc is not None:
            raise entry.exc[0]  # TODO Why [0] here, and not above?


    # Return
    # ======
    # The caller must take care to avoid mutating any context dictionary at
    # entry.resource.pages[0].

    return entry.resource
