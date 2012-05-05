import pystache
from aspen import renderers


class Renderer(renderers.Renderer):
    def render_content(self, context):
        return pystache.render(self.compiled, context)


class Factory(renderers.Factory):
    Renderer = Renderer
