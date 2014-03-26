"""
aspen.renderers.stdlib_template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import renderers
from string import Template

class Renderer(renderers.Renderer):
    def compile(self, filepath, raw):
        return Template(raw)

    def render_content(self, context):
        return self.compiled.substitute(context)


class Factory(renderers.Factory):
    Renderer = Renderer
