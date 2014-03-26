"""
aspen.renderers.json_dump
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import renderers
from aspen import json

class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        if 'Content-type' not in context['response'].headers:
            response = context['response']
            website = context['website']
            response.headers['Content-type'] = website.media_type_json
        return json.dumps(eval(self.compiled, globals(), context))


class Factory(renderers.Factory):
    Renderer = Renderer

