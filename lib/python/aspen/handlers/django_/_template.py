from os.path import isfile

from django.conf.urls.defaults import patterns # django must be on PYTHONPATH
from django.http import HttpResponse
from django.template import RequestContext, Template

from wsgi import WSGI # our imports are relative to support use outside aspen
from cache import Cache


# Register additional features
# ============================
# To get "extends," etc., we need to import the following.

from django.template import loader, loader_tags


# First define the WSGI side.
# ===========================

wsgi = WSGI() # wire this in __/etc/handlers.conf
wsgi.filetype = 'template'


# Then set up a cache.
# ====================

def build(fspath):
    """Given a filesystem path, return a compiled (but unbound) object.
    """
    return Template(open(fspath).read())


cache = Cache(build)


# Now define the Django side.
# ===========================

def view(request):
    """Django view to render the template at PATH_TRANSLATED.
    """
    fspath = request.META['PATH_TRANSLATED']
    template = cache[fspath]
    response = HttpResponse(template.render(RequestContext(request)))
    del response.headers['Content-Type'] # take this from the extension
    return response


urlpatterns = patterns('', (r'^', view)) # wired in WSGI, above
