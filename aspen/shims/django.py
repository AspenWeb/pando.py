"""
aspen.shims.django
++++++++++++++++++

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
import os

from aspen.request_processor import RequestProcessor
from aspen.simplates.renderers import Renderer, Factory
from django.conf import settings
from django.http import HttpResponse
from django.template import Template
from django.template.context import Context


class NoProjectRoot(Exception):
    pass


def install(*a, **kw):
    """Install Aspen into a Django app.
    """
    arp = kw.pop('_aspen_request_processor', None)
    if arp is None:

        # Infer project and www roots.
        default_project_root = None
        parent = inspect.stack()[1]
        if parent:
            default_project_root = os.path.dirname(parent[1])
        kw['project_root'] = kw.get('project_root', default_project_root)
        if kw['project_root'] is None:
            raise NoProjectRoot()
        kw['www_root'] = kw.get('www_root', os.path.join(kw['project_root'], 'www'))

        # Instantiate and configure.
        arp = RequestProcessor(*a, **kw)
        arp.renderer_factories['django'] = DjangoRendererFactory(arp)
        arp.default_renderers_by_media_type['text/html'] = 'django'
    return arp


class DjangoRenderer(Renderer):

    def compile(self, fspath, raw):
        return Template(raw)

    def render_content(self, context):
        context = Context(context)
        return self.compiled.render(context)


class DjangoRendererFactory(Factory):
    Renderer = DjangoRenderer


def view(request):
    arp = settings.ASPEN_REQUEST_PROCESSOR
    state = arp.process( request.path
                       , request.META.get('QUERY_STRING', '')
                       , request.META.get('HTTP_ACCEPT', None)
                       , request=request
                        )
    output = state['output']
    body = output.body
    if type(body) is not type(b''):
        assert output.charset
        body = body.encode(output.charset)
    return HttpResponse(content=body)
