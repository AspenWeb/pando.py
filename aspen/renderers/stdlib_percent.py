from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import renderers


class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        print(repr(self.compiled))
        return self.compiled % context


class Factory(renderers.Factory):
    Renderer = Renderer

