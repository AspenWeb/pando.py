"""This module provides WSGI apps for serving Django w/o urlconf madness.

The namespace for each is an extended Django RenderContext:

  http://www.djangobook.com/en/beta/chapter10/#cn62


Our main class here is wsgi.WSGI, a thin wrapper around BaseHandler.get_response
(WSGIHandler doesn't define the method), which hacks request.urlconf to use the
filesystem for site hierarchy rather than the settings module. Since Django
finds an urlconf based on a magic name within a module ('urlpatterns'), we need
a separate module for each type of file: script and template. That's the reason
for the layout of this package.

"""
import mimetypes
import os
from os.path import isfile

from aspen.handlers.simplate.cache import SimplateCache
from django.conf.urls.defaults import patterns
from django.core.handlers.wsgi import WSGIHandler
from django.http import HttpResponse
from django.template import RequestContext, Template


# Register additional features
# ============================
# To get "extends," etc., we need to import the following.

from django.template import loader, loader_tags


# If we have django, make sure we have a settings module.
# =======================================================

from django.core.exceptions import ImproperlyConfigured

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


# Enable the present module to fulfill Django's 'urlconf' contract.
# =================================================================

urlpatterns = patterns('', (r'^', wsgi.view))


# Define our class.
# =================

class DjangoSimplate(BaseSimplate, WSGIHandler):
    """Simplate implementation for the Django web framework.
    """


    # BaseSimplate
    # ============

    def compile_template(self, template):
        """
        """
        return Template(template)


    def view(self, request):
        """Django view to exec and render the simplate at PATH_TRANSLATED.

        We get here like this:

            aspen.website
            aspen.handlers
            django WSGI
            wacko urlconf override
            DjangoSimplate.view

        """
        fspath = request.META['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."

        namespace, script, template = self.load(fspath)
        namespace = namespace.copy() # don't mutate the cached version
        namespace['__file__'] = fspath

        template = Template(template)
        template_context = RequestContext(request, imports)

        if script:
            for d in template_context.dicts:
                namespace.update(d)
            try:
                exec script in namespace
            except SystemExit:
                pass

            template_context.update(namespace)


        if 'response' in namespace:
            response = namespace['response']
        else:
            response = HttpResponse(template.render(template_context))
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            response.headers['Content-Type'] = guess # doubles-up?

        return response


    # WSGIHandler
    # ===========

    def get_response(self, request):
        """Extend WSGIHandler.get_response to bypass usual Django urlconf.

        We could ask folks to do this in their settings.py. Is that better?

        """
        request.urlconf = 'aspen.handlers.simplates._django'
        return WSGIHandler.get_response(self, request)





wsgi = DjangoSimplate()
