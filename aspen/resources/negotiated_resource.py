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
import copy 

from aspen import Response
from aspen.resources.dynamic_resource import DynamicResource
from aspen._tornado.template import Template


class TemplateResource(DynamicResource):
    """This is a template resource. It has two or three pages.
    """

    min_pages = 2
    max_pages = 4

    def compile_third(self, one, two, three, padding):
        """Given three bytestrings, return a Template instance.

        This method depends on fs and website attributes on self.
        
        We used to take advantage of padding, but:

            a) Tornado templates have some weird error handling that we haven't
            exposed yet.
            
            b) It's counter-intuitive if your template resources show up in the
            browser with tons of whitespace at the beginning of them.

        """
        return Template( self._trim_initial_newline(three)
                       , name = self.fs
                       , loader = self.website.template_loader 
                       , compress_whitespace = False
                        )

    def compile_fourth(self, one, two, three, four, padding):
        """Given None, return None. Template resources have a noop fourth page.
        """
        four = four.replace('\r\n', '\n')
        four = padding + four
        four = compile(four, self.fs, 'exec')
        return four

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


    def get_response(self, namespace):
        """Given a namespace dict, return a response object.
        """
        response = namespace['response']
        response.body = self.three.generate(**namespace)
        if response.headers.one('Content-Type') is None:
            response.headers.set('Content-Type', self.mimetype)
        return response
