"""
aspen.shims.flask
+++++++++++++++++

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
import os

from aspen.request_processor import RequestProcessor
from aspen.simplates import renderers
from flask import request
from jinja2 import BaseLoader, Environment, FileSystemLoader


class NoProjectRoot(Exception):
    pass


def install(app, *a, **kw):
    """Install Aspen into a Flask app.
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

        # Instantiate.
        arp = RequestProcessor(*a, **kw)

    # Configure.
    arp.renderer_factories['jinja2'] = Jinja2RendererFactory(arp)
    arp.default_renderers_by_media_type['text/html'] = 'jinja2'

    # We can't use add_url_rule because it forces us to constrain methods.
    app.url_map.add(app.url_rule_class('/', endpoint='aspen', methods=None))
    app.view_functions['aspen'] = FlaskAspenView(app, arp)
    app._aspen_request_processor = arp

    return arp


def FlaskAspenView(app, arp):
    def view():
        state = arp.process( request.path
                           , request.query_string
                           , request.headers.get('HTTP_ACCEPT', None)
                           , app=app
                           , request=request
                            )
        output = state['output']
        body = output.body
        if type(body) is not type(b''):
            assert output.charset
            body = body.encode(output.charset)
        return body
    return view


"""Implement a Jinja2 renderer.

Jinja2 insists on unicode, and explicit loader objects. We assume with Jinja2
that your templates on the filesystem be encoded in UTF-8 (the result of the
template will be encoded to bytes for the wire per response.charset). We shim a
loader that returns the decoded content page and instructs Jinja2 not to
perform auto-reloading.

"""


class SimplateLoader(BaseLoader):
    """Jinja2 really wants to get templates via a Loader object.

    See: http://jinja.pocoo.org/docs/api/#loaders

    """

    def __init__(self, filepath, raw):
        self.filepath = filepath
        self.decoded = raw

    def get_source(self, environment, template):
        return self.decoded, self.filepath, True


class Jinja2Renderer(renderers.Renderer):
    """Renderer for jinja2 templates.

    Jinja2 is sandboxed, so only gets the context from simplate, not even
    access to python builtins.  Put any global functions or variables you
    want access to in your template into the 'global_context' here to have
    it passed along, augmented, of course, by the actual local context.

    For instance, if you want access to some python builtins, you might, in
    your configure-aspen.py put something like:

    website.renderer_factories['jinja2'].Renderer.global_context = {
            'range': range,
            'unicode': unicode,
            'enumerate': enumerate,
            'len': len,
            'float': float,
            'type': type
    }

    Clearly, by doing so, you're overriding jinja's explicit decision to not
    include those things by default, which may be fraught - but that's up to
    you.

    """
    global_context = {}

    def compile(self, filepath, raw):
        environment = self.meta
        return SimplateLoader(filepath, raw).load(environment, filepath)

    def render_content(self, context):
        charset = context['output'].charset
        # Inject globally-desired context
        context.update(self.global_context)
        return self.compiled.render(context).encode(charset)


class Jinja2RendererFactory(renderers.Factory):

    Renderer = Jinja2Renderer

    def compile_meta(self, configuration):
        loader = None
        if configuration.project_root is not None:
            # Instantiate a loader that will be used to resolve template bases.
            loader = FileSystemLoader(configuration.project_root)
        return Environment(loader=loader, autoescape=True)
