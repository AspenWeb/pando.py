
from __future__ import absolute_import
from aspen import renderers
import pystache


class Renderer(renderers.Renderer):
    def render_content(self, context):
        return pystache.render(self.raw, context)


class Factory(renderers.Factory):
    Renderer = Renderer
