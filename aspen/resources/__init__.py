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
import sys
import traceback

from aspen.exceptions import LoadError
from aspen.resources.json_resource import JSONResource
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.resources.rendered_resource import RenderedResource
from aspen.resources.socket_resource import SocketResource
from aspen.resources.static_resource import StaticResource

import watchdog
from watchdog.observers import Observer

try:                    # python2.6+
    from collections import namedtuple
except ImportError:     # < python2.6
    from backcompat import namedtuple

# Cache helpers
# =============

__cache__ = dict()  # cache, keyed to filesystem path

class Cache_Invalidator(watchdog.events.FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path in __cache__.keys():
            del __cache__[event.src_path]

CacheEntry = namedtuple('CacheEntry', 'resource exc' )

def watcher_for(path):
    """turn on resource watching for the specified path ; return the observer object"""
    watcher = Observer()
    watcher.schedule(Cache_Invalidator(), path=path, recursive=True)
    return watcher

# Core loaders
# ============

def load(request):
    """Given a Request, return a Resource object (w/o caching).
    """

    # Load bytes.
    # ===========
    # We work with resources exclusively as bytestrings. Renderers take note.

    raw = open(request.fs, 'rb').read()

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
    elif media_type == 'application/json':          # json
        Class = JSONResource
    elif media_type == 'application/x-socket.io':   # socket
        Class = SocketResource
    elif '.' in os.path.basename(guess_with):       # rendered
        Class = RenderedResource
    else:                                           # negotiated
        Class = NegotiatedResource

    resource = Class(request.website, request.fs, raw, media_type)
    return resource


def get(request):
    """Given a Request, return a Resource object (with caching).

    We need the request because it carries media_type_default.

    """

    # XXX This is not thread-safe. It used to be, but then I simplified it
    # when I switched to diesel. Now that we have multiple engines, some of
    # which are threaded, we need to make this thread-safe again.

    # Get a CacheEntry object.
    # =========================

    if request.fs not in __cache__:

        resource, exc = None, None

        # Process the resource.
        # =====================

        try:
            resource = load(request)
        except:     # capture any Exception
            exc = ( LoadError(traceback.format_exc())
                        , sys.exc_info()[2]
                         )

        __cache__[request.fs] = CacheEntry(resource=resource, exc=exc)

    entry = __cache__[request.fs]

    # Raise or Return just like we did the first time
    # ===============================================
    # The caller must take care to avoid mutating any context dictionary at
    # entry.resource.pages[0].

    if entry.exc is not None: # raise the captured exception, if any
        raise entry.exc

    return entry.resource

