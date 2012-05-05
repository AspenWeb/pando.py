import pystache
from aspen import renderers


class Renderer(renderers.Renderer):
    def render_content(self, context):
        return pystache.render(self.raw, context)


class Factory(renderers.Factory):
    Renderer = Renderer
