from os.path import isfile

from django import http # django must be on PYTHONPATH
from django.conf.urls.defaults import patterns
from django.template import RequestContext

from wsgi import WSGI # our imports are relative to support use outside aspen
from cache import Cache


# First define the WSGI side.
# ===========================

wsgi = WSGI() # wire this in __/etc/handlers.conf
wsgi.filetype = 'script'


# Then set up a cache.
# ====================

def build(fspath):
    """Given a filesystem path, return a compiled (but unbound) object.
    """
    return compile(open(fspath).read().replace('\r\n', '\n'), fspath, 'exec')


cache = Cache(build)


# Now define the Django side.
# ===========================

def view(request):
    """Django view to exec the script at PATH_TRANSLATED.
    """

    fspath = request.META['PATH_TRANSLATED']

    context = dict()
    for d in RequestContext(request).dicts:
        context.update(d)

    try:
        exec cache[fspath] in context
    except SystemExit:
        pass

    if 'response' not in context:
        raise LookupError("script %s does not define 'response'" % path)
    return context['response']

urlpatterns = patterns('', (r'^', view)) # wired in WSGI, above
