import pystache
from aspen import renderers


class Renderer(renderers.Renderer):
    def render_content(self, compiled, context):
        return pystache.render(compiled, context)


class Factory(renderers.Factory):
    Renderer = Renderer
