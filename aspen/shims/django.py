"""
aspen.shims.django
++++++++++++++++++


"""
from __future__ import absolute_import, division, print_function, unicode_literals

from aspen import dispatcher, resources, Response as AspenResponse
from aspen.renderers import Renderer, Factory
from django.conf import settings
from django.http import HttpResponse
from django.template import Template
from django.template.context import Context


def view(request):

    processor = settings.ASPEN_PROCESSOR

    pathparts = request.path.split('/')[1:]
    path = request.path
    querystring = request.META['QUERY_STRING']
    response = None

    try:
        result = dispatcher.dispatch( indices               = website.indices
                                    , media_type_default    = website.media_type_default
                                    , pathparts             = pathparts
                                    , uripath               = path
                                    , querystring           = querystring
                                    , startdir              = website.www_root
                                    , directory_default     = ''
                                    , favicon_default       = ''
                                     )
        context = { 'dispatch_result': result
                  , 'accept_header': request.META.get('HTTP_ACCEPT')
                  , 'request': request
                  , 'user': request.user
                   }
        simplate = resources.get(website, result.match)
        aspen_response = simplate.respond(context)
    except AspenResponse as aspen_response:
        pass
    except SystemExit as exc:
        response = exc.args[0]
        assert response is not None

    if response is None:
        response = HttpResponse()
        response.status_code = aspen_response.code
        for k, v in aspen_response.headers.items():
            for val in v:
                response[k] = val
        response.content = aspen_response.body

    return response


class DjangoRenderer(Renderer):

    def compile(self, fspath, raw):
        return Template(raw)

    def render_content(self, context):
        context = Context(context)
        return self.compiled.render(context)


class DjangoRendererFactory(Factory):
    Renderer = DjangoRenderer


def install(processor=None):
    if processor is None:
        processor = Processor()
    processor.renderer_factories['django'] = DjangoRendererFactory(processor)
    processor.default_renderers_by_media_type['text/html'] = 'django'
