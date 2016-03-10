"""
aspen.simplates.renderers.stdlib_percent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from . import Renderer, Factory


class Renderer(Renderer):
    def compile(self, filepath, raw):
        return raw

    def render_content(self, context):
        return self.compiled % context


class Factory(Factory):
    Renderer = Renderer

