from os.path import isfile

from django.conf.urls.defaults import patterns # django must be on PYTHONPATH
from django import http
from django.http import HttpResponse
from django.template import RequestContext, Template

from wsgi import WSGI # our imports are relative to support use outside aspen
from cache import Cache


FORM_FEED = chr(12) # ^L, ASCII page break


# Register additional features
# ============================
# To get "extends," etc., we need to import the following.

from django.template import loader, loader_tags


# First define the WSGI side.
# ===========================

wsgi = WSGI() # wire this in __/etc/handlers.conf
wsgi.filetype = 'scrimplate'


# Then set up a cache.
# ====================

def build(fspath):
    """Given a filesystem path, return a compiled (but unbound) object.

    A scrimplate is a template with an optional Python component at the head of
    the file, delimited by an ASCII form feed (also called a page break, FF, ^L,
    \x0c, 12). The Python section is exec'd within the template namespace before
    the template is rendered, giving you a chance to add custom stuff in there.

    """
    scrimplate = open(fspath).read()

    numff = scrimplate.count(FORM_FEED)
    if numff == 0:
        script = ""
        template = scrimplate
    elif numff == 1:
        script, template = scrimplate.split(FORM_FEED)
    else:
        raise SyntaxError( "Scrimplate <%s> may have at most one " % fspath
                         + "form feed; it has %d." % numff
                          )

    c_script = compile(script.replace('\r\n', '\n'), fspath, 'exec')
    c_template = Template(template)

    return (c_script, c_template)

cache = Cache(build)


# Now define the Django side.
# ===========================

def view(request):
    """Django view to exec and render the scrimplate at PATH_TRANSLATED.
    """
    script, template = cache[request.META['PATH_TRANSLATED']]

    template_context = RequestContext(request)

    if script:
        script_context = dict()
        for d in template_context.dicts:
            script_context.update(d)
        try:
            exec script in script_context
        except SystemExit:
            pass
        if 'response' in script_context:
            return script_context['response']
        template_context.update(script_context)

    return HttpResponse(template.render(template_context))


urlpatterns = patterns('', (r'^', view)) # wired in WSGI, above
