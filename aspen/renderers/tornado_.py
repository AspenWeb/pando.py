from aspen import renderers
from aspen._tornado.template import Loader, Template


class Renderer(renderers.Renderer):

    def compile(self, filepath, raw):
        loader = self.meta
        return Template(raw, filepath, loader, compress_whitespace=False)

    def render_content(self, context):
        return self.compiled.generate(**context)


class Factory(renderers.Factory):

    Renderer = Renderer

    def compile_meta(self, configuration):
        bases_dir = configuration.project_root
        if bases_dir is None:
            loader = None
        else:
            loader = Loader(bases_dir)
        return loader
