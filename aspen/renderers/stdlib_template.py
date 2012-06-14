from aspen import renderers
from string import Template

class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return Template(raw)

    def render_content(self, context):
        return self.compiled.substitute(context)


class Factory(renderers.Factory):
    Renderer = Renderer
