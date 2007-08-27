"""This little shim wires Aspen up to serve Django.
"""
import os
import sys

import aspen
from django.core.handlers.wsgi import WSGIHandler
from django.core.exceptions import ImproperlyConfigured


# Tell Django which settings to use.
# ==================================
# If DJANGO_SETTINGS_MODULE is set, just use that. Otherwise, set it from
# aspen.conf.

if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    settings_module = aspen.conf.django.get('settings_module', None)
    if settings_module is None:
        raise ImproperlyConfigured( "Please set DJANGO_SETTINGS_MODULE in "
                                  + "the environment or settings_module in "
                                  + "the [django] section of __/etc/aspen."
                                  + "conf."
                                   )
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_module


# Instantiate Django's WSGI handler.
# ==================================
# This is then wired up to the website root in __/etc/apps.conf.

_wsgi = WSGIHandler()
def wsgi(environ, start_response):
    """Trick Django into thinking that it owns the place.
    """
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    environ['SCRIPT_NAME'] = ''
    return _wsgi(environ, start_response)
