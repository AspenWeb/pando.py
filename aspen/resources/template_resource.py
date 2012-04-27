"""Template resources.

Problems with tornado.template:

    - no option to fail silently
    - Loader cache doesn't account for modtime
    - Is this a bug?

        {{ foo }}
        {% for foo in [1,2,3] %}
        {% end %}

    - no loop counters, eh? must do it manually with {% set %}
    - can't do this:

        {% if ... %}
            {% extends %}
        {% else %}
            {% extends %}
        {% end %}

"""
from aspen.resources.dynamic_resource import DynamicResource
from aspen._tornado.template import Template

PAGE_BREAK = chr(12)

class TemplateResource(DynamicResource):
    """This is a template resource. It has two or three pages.
    """

    min_pages = 2
    max_pages = 4

    def compile_page(self, page, padding):
        """Parse out the specline between ^L and \n, figure out the renderer and use it
        """
        if '\n' in page:
            specline, input = page.split('\n',1)
        else:
            specline, input = '', page
        renderer_name = self._parse_specline(specline)
        if renderer_name is None:
            renderer_name = self.website.template_loader_default
        if not renderer_name in self.website.template_loaders:
            raise TypeError("No renderer named '%s'." % renderer_name)
        renderer = self.website.template_loaders[renderer_name]
        template_root = self.website.project_root or self.website.www_root
        return renderer( template_root, self.fs, input )


    def _parse_specline(self, line):
        """parse out the specline

            ^L #!renderer

            return None for any parts unspecified on the specline
        """
        # TODO: enforce order
        line = line.strip('\n ' + PAGE_BREAK)
        renderer, content_type = None, None
        for arg in line.split(' '):
            if arg.startswith('#!'):
                renderer = arg[2:]
        return renderer


    def parse(self, raw):
        """if there's only two pages, there's only one logic page, so insert a blank one up front"""

        pages = DynamicResource.parse(self, raw)

        if len(pages) < 3:
            pages = [''] + pages

        return pages


    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        response = context['response']
        renderer = self.pages[0]
        response.body = renderer(**context)
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = self.mimetype
            if self.mimetype.startswith('text/'):
                charset = response.charset
                if charset is not None:
                    response.headers['Content-Type'] += '; charset=' + charset

        return response
