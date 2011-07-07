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
    """This is a template resource. It has one, two, or three pages.
    """

    def compile(self, npages, pages):
        """Given an int and a sequence of bytestrings, set attributes on self.
        """
        if npages == 2:
            one = ""
            two, three = pages
        elif npages == 3:
            one, two, three = pages
        else:
            raise SyntaxError( "Template resources may have at most three page"
                               "s; %s has %d." % (request.fs, npages)
                              )
       
        one, two = self.compile_python(one, two)
        three = self._trim_initial_newline(three)
        three = self._compile_template( three
                                      , self.fs
                                      , self.website.template_loader
                                       )
        self.one = one
        self.two = two
        self.three = three
  
    def _compile_template(self, template, name, loader):
        """Given a bytestring, return a Template instance.
        """
        return Template( template 
                       , name = name 
                       , loader = loader
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


    def mutate(self, namespace):
        """Given a namespace dict, mutate it.
        """
        response = namespace['response']
        response.body = self.three.generate(**namespace)
