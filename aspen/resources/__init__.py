"""
aspen.resources
+++++++++++++++

Aspen uses resources to model HTTP resources.

Here is the class hierarchy:

    Resource
     |
     +-- Simplate
     |
     +-- StaticResource

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mimetypes
import os
import re
import stat
import sys
import traceback

from aspen.backcompat import StringIO
from aspen.exceptions import LoadError
from aspen.resources.simplate import Simplate
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


def decode_raw(raw):
    """As per PEP 263, decode raw data according to the encoding specified in
       the first couple lines of the data, or in ASCII.  Non-ASCII data without
       an encoding specified will cause UnicodeDecodeError to be raised.
    """

    decl_re = re.compile(r'^[ \t\f]*#.*coding[:=][ \t]*([-\w.]+)')

    def get_declaration(line):
        match = decl_re.match(line)
        if match:
            return match.group(1)
        return None

    encoding = None
    fulltext = b''
    sio = StringIO(raw)
    for line in (sio.readline(), sio.readline()):
        potential = get_declaration(line)
        if potential is not None:
            if encoding is None:

                # If both lines match, use the first. This matches Python's
                # observed behavior.

                encoding = potential
                munged = b'# encoding set to {0}\n'.format(encoding)

            else:

                # But always munge any encoding line. We can't simply remove
                # the line, because we want to preserve the line numbering.
                # However, later on when we ask Python to exec a unicode
                # object, we'll get a SyntaxError if we have a well-formed
                # `coding: # ` line in it.

                munged = b'# encoding NOT set to {0}\n'.format(potential)

            line = line.split(b'#')[0] + munged

        fulltext += line
    fulltext += sio.read()
    sio.close()
    return fulltext.decode(encoding or b'ascii')


# Core loaders
# ============

def load(website, fspath, mtime):
    """Given a Request and a mtime, return a Resource object (w/o caching).
    """

    is_spt = fspath.endswith('.spt')

    # Load bytes.
    # ===========
    # .spt files are simplates, which get loaded according to their encoding
    #      and turned into unicode strings internally
    # non-.spt files are static, possibly binary, so don't get decoded

    with open(fspath, 'rb') as fh:
        raw = fh.read()
    if is_spt:
        raw = decode_raw(raw)

    # Compute a media type.
    # =====================
    # For a negotiated resource we will ignore this.

    guess_with = fspath
    if is_spt:
        guess_with = guess_with[:-4]
    fs_media_type = mimetypes.guess_type(guess_with, strict=False)[0]
    is_bound = fs_media_type is not None  # bound to a media type via file ext
    media_type = fs_media_type if is_bound else website.media_type_default


    # Compute and instantiate a class.
    # ================================
    # An instantiated resource is compiled as far as we can take it.

    Class = Simplate if is_spt else StaticResource
    resource = Class(website, fspath, raw, media_type, is_bound, mtime)
    return resource


def get(website, fspath):
    """Given a website and a filesystem path, return a Resource object (with caching).
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
            entry.resource = load(website, fspath, mtime)
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
