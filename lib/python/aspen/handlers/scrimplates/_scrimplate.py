import linecache
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
    within the template namespace each time the template is rendered.

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

    # Standardize newlines.
    # =====================
    # compile requires \n, and doing it now makes the next line easier.

    imports = imports.replace('\r\n', '\n')
    script = script.replace('\r\n', '\n')


    # Pad the beginning of the script section so we get accurate tracebacks.
    # ======================================================================

    script = ''.join(['\n' for n in range(imports.count('\n')-2)]) + script


    # Prep our cachable objects and return.
    # =====================================

    c_imports = dict()
    exec compile(imports, fspath, 'exec') in c_imports
    c_script = compile(script, fspath, 'exec')
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

    response = HttpResponse(template.render(template_context))
    del response.headers['Content-Type'] # take this from the extension
    return response


urlpatterns = patterns('', (r'^', view)) # wired in WSGI, above



"""This package provides WSGI apps for serving Django w/o urlconf madness.


The namespace for each is an extended Django RenderContext:

  http://www.djangobook.com/en/beta/chapter10/#cn62


The additional keys are:

  __file__      equivalent to PATH_TRANSLATED
  http          the django.http module [scripts only]
  request       the current Django HttpRequest object
  response      a Django HttpResponse object [scripts only]


Our main class here is wsgi.WSGI, a thin wrapper around BaseHandler.get_response
(WSGIHandler doesn't define the method), which hacks request.urlconf to use the
filesystem for site hierarchy rather than the settings module. Since Django
finds an urlconf based on a magic name within a module ('urlpatterns'), we need
a separate module for each type of file: script and template. That's the reason
for the layout of this package.

"""
import os


__all__ = ['script', 'template', 'scrimplate']


try:
    import django

except ImportError:

    # If no django, set up a dummy.
    # =============================

    def wsgi(environ, start_response):
        # This should probably raise at import time, but that would take more
        # work to not trigger in our tests.
        raise NotImplementedError("django is not on PYTHONPATH")
    script = template = scrimplate = wsgi

else:

    # If we have django, find the settings module.
    # ============================================

    from django.core.exceptions import ImproperlyConfigured

    try:
        import aspen
    except ImportError:
        raise
    else:
        if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
            settings_module = aspen.conf.django.get('settings_module', None)
            if settings_module is None:
                raise ImproperlyConfigured( "Please set DJANGO_SETTINGS_MODULE "
                                          + "in the environment or "
                                          + "settings_module in the [django] "
                                          + "section of __/etc/aspen.conf."
                                           )
            else:
                os.environ['DJANGO_SETTINGS_MODULE'] = settings_module



