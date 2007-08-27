"""This module provides WSGI apps for serving Django w/o urlconf madness.

The namespace for a Django template is an extended Django RenderContext:

  http://www.djangobook.com/en/beta/chapter10/#cn62

"""
import mimetypes
import os
from os.path import isfile

from aspen.apps import django_ # may raise ImproperlyConfigured
from aspen.handlers.simplates.base import BaseSimplate
from django.conf.urls.defaults import patterns
from django.core.handlers.wsgi import WSGIHandler
from django.http import HttpResponse
from django.template import RequestContext, Template


# Register additional features
# ============================
# To get "extends," etc., we need to import the following.

from django.template import loader, loader_tags


# Define our class.
# =================

class DjangoSimplate(WSGIHandler, BaseSimplate):
    """Simplate implementation for the Django web framework.
    """

    def __init__(self):
        WSGIHandler.__init__(self)
        BaseSimplate.__init__(self)


    # BaseSimplate
    # ============

    def compile_template(self, template):
        """
        """
        return Template(template)


    def view(self, request): # under __call__
        """Django view to exec and render the simplate at PATH_TRANSLATED.

        We get here like this:

            aspen.website:Website.__call__
            aspen.handlers.simplates.django_:DjangoSimplate.__call__
              [i.e., django.core.handlers.wsgi:WSGIHandler.__call__]
            <your_project>.urls:urlpatterns
            aspen.handlers.simplates.django_:DjangoSimplate.view

        """

        # 1. Check for file
        # =================

        fspath = request.META['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."


        # 2. Load simplate
        # ================

        namespace, script, template = self.load_simplate(fspath)


        # 3. Populate namespace
        # =====================
        # Django templates can't take a straight dict.

        template_context = RequestContext(request, namespace)


        # 4. Run the script
        # =================

        WANT_TEMPLATE = True
        response = None
        if script:
            for d in template_context.dicts:
                namespace.update(d)
            try:
                exec script in namespace
            except SystemExit, exc:
                if len(exc.args) > 0:
                    r = exc.args[0]
                    if isinstance(r, HttpResponse):
                        response = r
                WANT_TEMPLATE = False
            template_context.update(namespace)


        # 5. Get a response
        # =================

        if response is None:
            if 'response' in namespace:
                response = namespace['response']
            else:
                response = HttpResponse()


        # 6. Render the template
        # ======================

        if WANT_TEMPLATE:
            response.write(template.render(template_context))
            headers = [h.lower() for h in response.headers.keys()]
            if 'content-type' not in headers:
                guess = mimetypes.guess_type(fspath, 'text/plain')[0]
                response.headers['Content-Type'] = guess


        # 7. Return
        # =========

        return response


wsgi = DjangoSimplate()


# Enable the present module to fulfill Django's 'urlconf' contract.
# =================================================================
# This is the basis of our hack to circumvent Django's URL routing without also
# cutting out all of its other frameworky goodness.

urlpatterns = patterns('', (r'^', wsgi.view))
