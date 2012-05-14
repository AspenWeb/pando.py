# -*- coding: utf-8 -*-

from aspen import renderers

from jinja2 import BaseLoader, TemplateNotFound, Environment, FileSystemLoader, ChoiceLoader, Template

"""
Jinja2 renderer

Supports template inheritance from www_root and project_root

Templates are cached by Jinja2 
"""

class SimplateLoader(FileSystemLoader):

    def get_source(self, environment, template):
        """
        TODO: more reliable simplate splitting
        """
        contents, filename, uptodate = super(SimplateLoader, self).get_source(environment, template)
        if contents.find('\f') != -1:
            simplate = contents.split('\f')
            header, contents = simplate[-1].split('\n', 1)
        elif contents.find('^L') != -1:
            simplate = contents.split('^L')
            header, contents = simplate[-1].split('\n', 1)
        return contents, filename, uptodate

class Renderer(renderers.Renderer):
    
    def compile(self, filepath, raw):
        """
        TODO: more reliable filepath normalization (changing filepath to be relative to root and not absolute)
        """
        filepath = filepath.replace(self.meta['configuration'].www_root, '')
        filepath = filepath.replace(self.meta['configuration'].project_root, '')
        return self.meta['jinja2_env'].get_template(filepath)

    def render_content(self, context):
        return self.compiled.render(context).encode(self.meta['configuration'].charset_dynamic)

class Factory(renderers.Factory):

    Renderer = Renderer

    def __init__(self, configuration):
        self.jinja2_env = Environment(loader=ChoiceLoader([
            SimplateLoader(configuration.www_root, encoding=configuration.charset_dynamic), # Simplate splittin' loader
            FileSystemLoader(configuration.project_root, encoding=configuration.charset_dynamic) # For base templates use the regular loader
            ]))
        super(Factory, self).__init__(configuration)

    def compile_meta(self, configuration):
        return {
            'configuration' : configuration,
            'jinja2_env' : self.jinja2_env}
