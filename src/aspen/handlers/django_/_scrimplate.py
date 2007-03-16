from os.path import isfile

from django.conf.urls.defaults import patterns # django must be on PYTHONPATH
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

    A scrimplate is a template with two optional Python components at the head
    of the file, delimited by an ASCII form feed (also called a page break, FF,
    ^L, \x0c, 12). The first Python section is exec'd when the scrimplate is
    first called, and the namespace it populates is saved for all subsequent
    runs (so make sure it is thread-safe!). The second Python section is exec'd
    within the template namespace before the template is rendered, giving you a
    chance to add custom stuff in there.

    Since RequestContext doesn't actually combine dictionaries on update, we
    don't have to worry about the import context being mutated at runtime.

    """
    scrimplate = open(fspath).read()

    numff = scrimplate.count(FORM_FEED)
    if numff == 0:
        script = imports = ""
        template = scrimplate
    elif numff == 1:
        imports = ""
        script, template = scrimplate.split(FORM_FEED)
    elif numff == 2:
        imports, script, template = scrimplate.split(FORM_FEED)
    else:
        raise SyntaxError( "Scrimplate <%s> may have at most two " % fspath
                         + "form feeds; it has %d." % numff
                          )

    c_imports = dict()
    exec compile(imports.replace('\r\n', '\n'), fspath, 'exec') in c_imports
    c_script = compile(script.replace('\r\n', '\n'), fspath, 'exec')
    c_template = Template(template)

    return (c_imports, c_script, c_template)

cache = Cache(build)


# Now define the Django side.
# ===========================

def view(request):
    """Django view to exec and render the scrimplate at PATH_TRANSLATED.

    Your script section may raise SystemExit to terminate execution. Instantiate
    the SystemExit with an HttpResponse to bypass template rendering entirely;
    in all other cases, the template section will still be rendered.

    """
    imports, script, template = cache[request.META['PATH_TRANSLATED']]

    template_context = RequestContext(request, imports)

    if script:
        script_context = dict()
        for d in template_context.dicts:
            script_context.update(d)
        try:
            exec script in script_context
        except SystemExit, exc:
            if len(exc.args) >= 1:
                response = exc.args[0]
                if isinstance(response, HttpResponse):
                    return response
        template_context.update(script_context)

    return HttpResponse(template.render(template_context))


urlpatterns = patterns('', (r'^', view)) # wired in WSGI, above
