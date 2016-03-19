"""
pando.simplates.renderers.json_dump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from . import Renderer, Factory
from ... import json

class Renderer(Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        if 'Content-type' not in context['response'].headers:
            response = context['response']
            website = context['website']
            response.headers['Content-type'] = website.media_type_json
        return json.dumps(eval(self.compiled, globals(), context))


class Factory(Factory):
    Renderer = Renderer

