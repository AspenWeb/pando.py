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


class TemplateResource(DynamicResource):
    """This is a template resource. It has two or three pages.
    """

    min_pages = 2
    max_pages = 4

    def compile_page(self, page, padding):
        """Given a bytestrings, return a Template instance.

        This method depends on fs and website attributes on self.
        
        We used to take advantage of padding, but:

            a) Tornado templates have some weird error handling that we haven't
            exposed yet.
            
            b) It's counter-intuitive if your template resources show up in the
            browser with tons of whitespace at the beginning of them.

        """
        return Template( self._trim_initial_newline(page)
                       , name = self.fs
                       , loader = self.website.template_loader
                       , compress_whitespace = False
                        )

    def _trim_initial_newline(self, template):
        """Trim any initial newline from page three.
        
        This is a convenience. It's nice to put ^L on a line by itself, but
        really you want the template to start on the next line.

        """
        try:
            if template[0] == '\r':     # Windows
                if template[1] == '\n':
                    template = template[2:]
            elif template[0] == '\n':   # Unix
                template = template[1:]
        except IndexError:              # empty template
            pass
        return template


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
        response.body = self.pages[0].generate(**context)
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = self.mimetype
            if self.mimetype.startswith('text/'):
                charset = response.charset
                if charset is not None:
                    response.headers['Content-Type'] += '; charset=' + charset

        return response
