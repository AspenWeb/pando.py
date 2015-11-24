"""
aspen.simplates.renderers.json_dump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from . import Renderer, Factory
from .. import json

class Renderer(Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        output = context['output']
        if not output.media_type:
            output.media_type = context['website'].media_type_json
        return json.dumps(eval(self.compiled, globals(), context))


class Factory(Factory):
    Renderer = Renderer

