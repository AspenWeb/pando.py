"""Simplates

Problems with tornado.template:

    - no option to fail silently
    - Loader cache doesn't account for modtime
    - Is this a bug?

    {{ foo }}
    {% for foo in [1,2,3] %}
    {% end %}

"""
import logging
import mimetypes
import os
import stat
import sys
import traceback

from aspen.http import Response
from _tornado.template import Loader, Template


FORM_FEED = chr(12) # == '\x0c', ^L, ASCII page break
ENCODING = 'UTF-8'
log = logging.getLogger('aspen.simplate')

# relax some mimetypes
for ext in ('py', 'sh'):
    mimetypes.add_type('text/plain', '.'+ext)
mimetypes.add_type('image/x-icon', '.ico') # this is for Python < 2.7


class LoadError(StandardError):
    """Represent a problem parsing a simplate.
    """


# Cache helpers
# =============

__cache = dict()        # cache

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

def load_uncached(request):
    """Given a Request object, return three objects (uncached).

    A simplate is a template with two optional Python components at the head of
    the file, delimited by '^L'. The first Python section is exec'd when the
    simplate is first called, and the namespace it populates is saved for all
    subsequent runs. The second Python section is exec'd within the template
    namespace each time the template is rendered.

    If the mimetype does not start with 'text/', then it is only a simplate if
    it has at least one form feed in it. Binary files generally can't be
    decoded using UTF-8. If Python's mimetypes module doesn't know about a
    certain extension, then we default to a configurable value (default is
    text/plain).

    """

    simplate = open(request.fs).read()
    
    mimetype = mimetypes.guess_type(request.fs, 'text/plain')[0]
    if mimetype is None:
        mimetype = request.conf.aspen.get('default_mimetype', 'text/plain')
    if not mimetype.startswith('text/'):
        s = lambda s: simplate.startswith(s)
        if not (s('#!') or s('"""') or s('import') or s('from')):
            # I tried checking for 1 or 2 FORM_FEEDs, but found a binary file
            # in the wild that indeed had exactly two. Let's sniff the first
            # few bytes.
            return (mimetype, None, None, simplate) # static file; exit early

    simplate = simplate.decode(ENCODING)


    nform_feeds = simplate.count(FORM_FEED)
    if nform_feeds == 0:
        script = imports = ""
        template = simplate
    elif nform_feeds == 1:
        imports = ""
        script, template = simplate.split(FORM_FEED)
    elif nform_feeds == 2:
        imports, script, template = simplate.split(FORM_FEED)
    else:
        raise SyntaxError( "Simplate <%s> may have at most two " % request.fs
                         + "form feeds; it has %d." % nform_feeds
                          )


    # Standardize newlines.
    # =====================
    # compile requires \n, and doing it now makes the next line easier.

    imports = imports.replace('\r\n', '\n')
    script = script.replace('\r\n', '\n')


    # Pad the beginning of the script and template sections.
    # ======================================================
    # This is so we get accurate tracebacks.

    script = ''.join(['\n' for n in range(imports.count('\n'))]) + script
    template = ''.join(['\n' for n in range(script.count('\n'))]) + template


    # Prep our cachable objects and return.
    # =====================================

    namespace = dict()
    namespace['__file__'] = request.fs
    script = compile(script, request.fs, 'exec')
    if template.strip():
        loader = Loader(os.path.join( request.root
                                    , '.aspen'
                                    , 'etc'
                                    , 'templates'
                                     ))
        template = Template( template
                           , name = request.fs
                           , loader = loader
                           , compress_whitespace = False
                            )
    else:
        template = None

    exec compile(imports, request.fs, 'exec') in namespace

    return (mimetype, namespace, script, template)


# Cache wrapper
# =============

def load(request):
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
            raise entry.exc[0]


    # Return
    # ======
    # Avoid mutating the cached namespace dictionary.

    mimetype, namespace, script, template = entry.quadruple
    if namespace is not None:
        namespace = namespace.copy()
    return (mimetype, namespace, script, template)


# Main callable.
# ==============

def handle(request, response=None):
    """Given a Request, return or raise a Response.
    """
    if response is None:
        response = Response()

    mimetype, namespace, script, template = load(request)

    if namespace is None:
        response.body = template
    else:
       
        # Populate namespace.
        # ===================
    
        namespace['request'] = request
        namespace['response'] = response
   

        # Exec the script.
        # ================
    
        if script:
            exec script in namespace
            response = namespace['response']


        # Process the template.
        # =====================
        # If template is None that means that that section was empty.
    
        if template is not None:
            response.body = template.generate(**namespace).encode(ENCODING)


    # Set the mimetype.
    # =================
    # Note that we guess based on the filesystem path, not the URL path.
    
    if response.headers.one('Content-Type') is None:
        if mimetype.startswith('text/'):
            mimetype += "; charset=" + ENCODING
        response.headers.set('Content-Type', mimetype)


    # Send it on back up the line.
    # ============================

    return response
