"""
aspen.resources
+++++++++++++++

Aspen uses resources to model HTTP resources.

Here is the class hierarchy:

    Resource                            Logic Pages     Content Pages
     +-- DynamicResource                -----------------------------
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
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.resources.rendered_resource import RenderedResource
from aspen.resources.socket_resource import SocketResource
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
    """Decode raw data according to the encoding specified in the first
       couple lines of the data, or in ASCII.  Non-ASCII data without an
       encoding specified will cause UnicodeDecodeError to be raised.
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

def load(request, mtime):
    """Given a Request and a mtime, return a Resource object (w/o caching).
    """

    is_spt = request.fs.endswith('.spt')

    # Load bytes.
    # ===========
    # .spt files are simplates, which get loaded according to their encoding
    #      and turned into unicode strings internally
    # non-.spt files are static, possibly binary, so don't get decoded

    with open(request.fs, 'rb') as fh:
        raw = fh.read()
    if is_spt:
        raw = decode_raw(raw)

    # Compute a media type.
    # =====================
    # For a negotiated resource we will ignore this.

    guess_with = request.fs
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
    elif media_type == 'application/x-socket.io':   # socket
        Class = SocketResource
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
