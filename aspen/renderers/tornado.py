from __future__ import absolute_import
from aspen import renderers
from tornado.template import Loader, Template
import os


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
            loader = LoaderShim(bases_dir)
        return loader


class LoaderShim(Loader):
    """
    The Tornado loader doesn't properly detect absolute Windows paths when
    resolving a template's path. This shim adds portable absolute path
    detection, falling back to the original Loader for relative paths.
    """

    def resolve_path(self, name, parent_path=None):
        # This is the inverse of the test Tornado's Loader.resolve_path() does
        # on a template's name and its parent's name. Tornado only tests for
        # absolute paths by looking for '/', which fails on Windows. If it
        # detects an absolute path it returns the name unmodified, so we defer
        # to the Tornado implementation if the path isn't absolute.
        if not parent_path or parent_path.startswith("<") or \
                os.path.isabs(parent_path) or os.path.isabs(name):
            return name

        return super(LoaderShim, self).resolve_path(name, parent_path)
