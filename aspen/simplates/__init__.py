"""Simplates are the main attraction.

Problems with tornado.template:

    - no option to fail silently
    - Loader cache doesn't account for modtime
    - Is this a bug?

        {{ foo }}
        {% for foo in [1,2,3] %}
        {% end %}

    - no loop counters, eh? must do it manually with {% set %}
    - can't do this:

        {% if ... %}
            {% extends %}
        {% else %}
            {% extends %}
        {% end %}

"""
import datetime
import logging
import mimetypes
import os
import stat
import sys
import traceback
from os.path import join

PAGE_BREAK = chr(12)

from aspen import json, Response
from aspen.simplates.simplate import Simplate
from aspen._tornado.template import Loader, Template


log = logging.getLogger('aspen.simplates')


class LoadError(StandardError):
    """Represent a problem parsing a simplate.
    """

class FriendlyEncoder(json.JSONEncoder):
    """Add support for additional types to the default JSON encoder.
    """

    def default(self, obj):
        if isinstance(obj, complex):
            # http://docs.python.org/library/json.html
            out = [obj.real, obj.imag]
        elif isinstance(obj, datetime.datetime):
            # http://stackoverflow.com/questions/455580/
            out = obj.isoformat()
        else:
            out = json.JSONEncoder.default(self, obj)
        return out


# Cache helpers
# =============

__cache = dict()        # cache, keyed to filesystem path

class Entry:
    """An entry in the global simplate cache.
    """

    fspath = ''         # The filesystem path [string]
    modtime = None      # The timestamp of the last change [int]
    quadruple = None    # A post-processed version of the data [4-tuple]
    exc = None          # Any exception in reading or compilation [Exception]

    def __init__(self):
        self.fspath = ''
        self.modtime = 0
        self.quadruple = ()


# Core loader
# ===========

def load(request):
    """Given a Request object, return four objects.

    A simplate is a template with two optional Python components at the head of
    the file, delimited by '^L'. The first Python page is exec'd when the
    simplate is first called, and the namespace it populates is saved for all
    subsequent runs. The second Python page is exec'd within the template
    namespace each time the template is rendered.

    If the mimetype does not start with 'text/', then it is only a simplate if
    it has at least one form feed in it. Binary files generally can't be
    decoded using UTF-8. If Python's mimetypes module doesn't know about a
    certain extension, then we default to a configurable value (default is
    text/plain).

    """

    raw = open(request.fs).read()
    
    # We work with simplates exclusively as a bytestring. Any unicode objects
    # passed in by the user as {{ expressions }} will be encoded with UTF-8 by
    # Tornado.
    
    mimetype = mimetypes.guess_type(request.fs, strict=False)[0]
    if mimetype is None:
        mimetype = request.default_mimetype
  

    # Try to exit early.
    # ==================
    # For non-simplates we want to return None for the first two pages, to
    # avoid those execs during request handling (this is an optimization).

    is_simplate = True # guilty until proven innocent

    if mimetype == 'application/x-socket.io':
        
        # *.sock files are always simplates.

        pass 

    elif mimetype.startswith('text/') or mimetype == 'application/json':

        # For text formats we can perform a highly accurate test for
        # simplitude.

        c = lambda s: s in raw
        is_simplate = c("") or c("^L") or c("{%") or c("{{")

    else:

        # For binary formats we must rely on a less-accurate test. This is
        # because a binary file can have s in it without being a simplate--
        # and I've actually seen, in the wild, a file with exactly two s. So
        # we sniff the first few bytes.

        s = lambda s: raw.startswith(s)
        is_simplate = s('"""') or s('import') or s('from')
           

    if not is_simplate:
        # Static files have no Python pages.
        return (mimetype, None, None, raw) 
    

    # Parse as a simplate.
    # ====================

    if mimetype == 'application/json':
        # http://aspen.io/simplates/json/
        simplate = JSONSimplate(raw)
    elif mimetype == 'application/x-socket.io':
        # http://aspen.io/simplates/socket/
        simplate = SocketSimplate(raw)
    else:
        # http://aspen.io/simplates/
        simplate = Simplate(raw)


    # Exec Python pages if they exist.
    # ================================
    # An imports page can't exist without a script page. If there are no Python
    # pages then we want to serve the file statically (namespace is None).

    namespace = None

    if simplate.two is not None: 

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        simplate.one = simplate.one.replace('\r\n', '\n')
        simplate.two = simplate.two.replace('\r\n', '\n')


        # Pad the beginning of the second page.
        # =====================================
        # This is so we get accurate tracebacks. We used to do this for the
        # template page too, but Tornado templates have some weird error 
        # handling that we haven't exposed yet.

        script = ''.join(['\n' for n in range(imports.count('\n'))]) + script


        # Prep our cachable objects and return.
        # =====================================

        namespace = dict()
        namespace['__file__'] = request.fs
        namespace['website'] = request.website
        script = compile(script, request.fs, 'exec')
        if template is not None:
            template = Template( template
                               , name = request.fs
                               , loader = request.website.template_loader
                               , compress_whitespace = False
                                )
        else:
            template = None

        exec compile(imports, request.fs, 'exec') in namespace

    return (mimetype, namespace, script, template)


# Cache wrapper
# =============

def get_simplate(request):
    """Given a Request object, return four objects (with caching).
    """

    # Get a cache Entry object.
    # =========================

    if request.fs not in __cache:
        entry = Entry()
        #entry.fspath = request.fs # TODO: What was this for?
        __cache[request.fs] = entry

    entry = __cache[request.fs]


    # Process the simplate.
    # =====================

    modtime = os.stat(request.fs)[stat.ST_MTIME]
    if entry.modtime == modtime:                            # cache hit
        if entry.exc is not None:
            raise entry.exc
    else:                                                   # cache miss
        try:
            entry.quadruple = load_uncached(request)
        except Exception, exception:
            # NB: Old-style string exceptions will still raise.
            entry.exc = ( LoadError(traceback.format_exc())
                        , sys.exc_info()[2]
                         )
        else: # reset any previous exception
            entry.exc = None 

        entry.modtime = modtime
        if entry.exc is not None:
            raise entry.exc[0] # TODO Why [0] here, and not above?


    # Return
    # ======
    # Avoid mutating the cached namespace dictionary.

    mimetype, namespace, script, template = entry.quadruple
    if namespace is not None:
        namespace = namespace.copy()
    return (mimetype, namespace, script, template)


