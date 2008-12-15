"""This module provides WSGI apps for serving Django w/o urlconf madness.

The namespace for a Django template is an extended Django RenderContext:

  http://www.djangobook.com/en/beta/chapter10/#cn62

"""
import mimetypes
import os
from os.path import exists, isfile


# Import gymnastics to support GAE as well as Aspen.
# ==================================================

try:
    from aspen.apps import django_ # may raise ImproperlyConfigured
except:
    DJANGO_SETTINGS_MODULE = 'settings' # @@ unhardcode
    os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE
try:
    from aspen.handlers.simplates.base import BaseSimplate
except:
    from simplates.base import BaseSimplate


from django.conf import settings
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
        # @@: Why are we doing this? --cwlw 2008-04-10
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
        WANT_CONTENT_TYPE = True
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
                        WANT_CONTENT_TYPE = False
            template_context.update(namespace)


        # 5. Get a response
        # =================
        # First, explicit response, then, raised response, lastly, implicit.

        if 'response' in namespace:             # explicit
            response = namespace['response']
            WANT_CONTENT_TYPE = False
        elif response is None:                  # raised? (per above)
            response = HttpResponse()           # implicit


        # 6. Render the template
        # ======================
        # Django 0.96 through trunk:6670 defaults to text/html, so if the user
        # doesn't provide an explicit response object (either by defining it
        # in the namespace or raising it w/ SystemExit) then we guess the
        # mimetype from the filename extension, and we take the charset from
        # Django settings.

        if WANT_TEMPLATE:
            response.write(template.render(template_context))

        if WANT_CONTENT_TYPE:
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            if guess is None:
                guess = settings.DEFAULT_CONTENT_TYPE
            if guess.startswith('text/'):
                guess += "; charset=%s" % settings.DEFAULT_CHARSET
            response['Content-Type'] = guess


        # 7. Return
        # =========

        return response


wsgi = DjangoSimplate()


# Enable the present module to fulfill Django's 'urlconf' contract.
# =================================================================
# This is the basis of our hack to circumvent Django's URL routing without also
# cutting out all of its other frameworky goodness.

urlpatterns = patterns('', (r'^', wsgi.view))


# Enable the present module also to fulfill Google App Engine's script API.
# =========================================================================

def gae_middleware(next):
    """Look for defaults, set PATH_TRANSLATED, ensure the file exists.

    This stuff is all duplicated from aspen for standalonability.

    """
    import logging
    import settings # @@: remove hardcode
    from simplates import _path_utils

    ROOT_PATH = os.path.dirname(settings.__file__) # @@: remove hardcode
    DYN_PATH = os.path.join(ROOT_PATH, 'dyn') # @@: remove hardcode

    def wsgi(environ, start_response):

        fspath = _path_utils.translate(DYN_PATH, environ['PATH_INFO'])
        _path_utils.check_trailing_slash(environ, start_response)
        fspath = _path_utils.find_default(['index.html'], fspath)

        if not exists(fspath):
            logging.info("Request for missing file: %s" % fspath)
            start_response('404 Not Found', [])
            response = ['Resource not found.']
        else:
            environ['PATH_TRANSLATED'] = fspath
            response = next(environ, start_response)

        return response

    return wsgi


def main():
    """http://code.google.com/appengine/articles/django.html
    """
    import logging
    import os

    from google.appengine.ext.webapp import util


    # Force Django to reload its settings.
    from django.conf import settings
    settings._target = None

    # Must set this env var before importing any part of Django
    os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE

    import django.core.handlers.wsgi
    import django.core.signals
    import django.db
    import django.dispatch.dispatcher

    def log_exception(*args, **kwds):
        logging.exception('Exception in request:')

    # Log errors.
    django.dispatch.dispatcher.connect( log_exception
                                     , django.core.signals.got_request_exception
                                        )

    # Unregister the rollback event handler.
    django.dispatch.dispatcher.disconnect( django.db._rollback_on_exception
                                     , django.core.signals.got_request_exception
                                          )


    util.run_wsgi_app(gae_middleware(wsgi))

