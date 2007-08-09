from aspen.handlers.simplate._wsgi import Simplate



class DjangoSimplate(Simplate):
    pass




wsgi = DjangoSimplate()




from django.conf.urls.defaults import patterns # django must be on PYTHONPATH
from django.http import HttpResponse
from django.template import RequestContext, Template



# Register additional features
# ============================
# To get "extends," etc., we need to import the following.

from django.template import loader, loader_tags


# First define the WSGI side.
# ===========================

wsgi = WSGI() # wire this in __/etc/handlers.conf
wsgi.filetype = 'scrimplate'



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




    def view(self, request):
        """Django view to exec and render the simplate at PATH_TRANSLATED.

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


import mimetypes
from os.path import isfile

from django.core.handlers.wsgi import WSGIHandler


class WSGI(WSGIHandler):
    """This WSGI app serves PATH_TRANSLATED as a Django script or template.
    """

    filetype = '' # 'script' or 'template' or 'scrimplate'

    def get_response(self, request):
        """Extend WSGIHandler.get_response to bypass usual Django urlconf.
        """
        fspath = request.META['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."
        request.urlconf = 'aspen.handlers.django_._' + self.filetype
        response = WSGIHandler.get_response(self, request)
        if 'Content-Type' not in response.headers:
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            response.headers['Content-Type'] = guess
        return response


