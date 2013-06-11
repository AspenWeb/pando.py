from aspen import renderers


class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        return self.compiled.format(**context)


class Factory(renderers.Factory):
    Renderer = Renderer
