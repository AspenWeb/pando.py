from aspen import renderers


class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return raw.decode(errors='ignore')

    def render_content(self, context):
        return self.compiled % context


class Factory(renderers.Factory):
    Renderer = Renderer
