"""
aspen.resources
+++++++++++++++

This is a registry of filesystem paths to objects representing HTTP resources.

Use :py:func:`get` to use the cache, use :py:func:`load` to circumvent it.

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

from .http.resource import Dynamic, Static


__cache__ = dict()  # cache, keyed to filesystem path


class LoadError(Exception):
    """Represent a problem loading a resource.
    """


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


def get(request_processor, fspath):
    """Given a RequestProcessor and a filesystem path, return a Resource object (with caching).
    """

    # XXX This is not thread-safe. It used to be, but then I simplified it
    # when I switched to diesel. Now that we have multiple engines, some of
    # which are threaded, we need to make this thread-safe again.

    # Get a cache Entry object.
    # =========================

    if fspath not in __cache__:
        entry = Entry()
        __cache__[fspath] = entry

    entry = __cache__[fspath]


    # Process the resource.
    # =====================

    mtime = os.stat(fspath)[stat.ST_MTIME]
    if entry.mtime == mtime:  # cache hit
        if entry.exc is not None:
            raise entry.exc
    else:  # cache miss
        try:
            entry.resource = load(request_processor, fspath, mtime)
        except:  # capture any Exception
            entry.exc = (LoadError(traceback.format_exc()), sys.exc_info()[2])
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


def load(request_processor, fspath, mtime):
    """Given a RequestProcessor, an fspath, and an mtime, return a Resource object (w/o caching).
    """

    is_spt = fspath.endswith('.spt')

    # Load bytes.
    # ===========
    # .spt files are simplates, which get loaded according to their encoding
    #      and turned into unicode strings internally
    # non-.spt files are static, possibly binary, so don't get decoded

    with open(fspath, 'rb') as fh:
        raw = fh.read()

    # Compute a media type.
    # =====================
    # For a negotiated resource we will ignore this.

    guess_with = fspath
    if is_spt:
        guess_with = guess_with[:-4]
    fs_media_type = mimetypes.guess_type(guess_with, strict=False)[0]
    media_type = fs_media_type if fs_media_type else request_processor.media_type_default

    # Compute and instantiate a class.
    # ================================
    # An instantiated resource is compiled as far as we can take it.

    Class = Dynamic if is_spt else Static
    return Class(request_processor, fspath, raw, media_type)
