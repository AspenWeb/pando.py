"""Negotiated resources

One not uncommon desire is to multiplex content types on a single HTTP
endpoint via content negotiation. Aspen should support this. Here's how
we want to do it.

If a file has no file extension, then it will be handled as a
"negotiated resource" ("simplate" is the file format, "resource" is the
thing defined by a simplate).

Negotiated resources should degrade such that a file is transparently
served as the first mime-type specified in the simplate

The format of the file is like this:

import foo
^L
data = foo.bar(request)
^L text/plain
{{ data }}
^L text/json
{{ json.dumps(data) }}

We have vendored in Joe Gregorio's content negotiation library ( http://code.google.com/p/mimeparse/source/browse/trunk/mimeparse.py ) to do the heavy lifting. This is in parallel to how we handle _cherrypy and _tornado vendoring.

This should also satisfy those who don't like inferring mimetypes from
file extensions. This would render as html:

/foo/bar

import foo
^L
hey = foo.bar(request)
^L text/html
<h1>{{ hey }}</h1>

Later:

If a file *does* have a file extension (foo.html), then it is a template
resource with a mimetype that matches the file extension

It is an error for a file to have both an extension *and* multiple template sections.

Given:

content 'single':

"global section"
import example
^L
"per-hit section"
data = "foo"
^L
{{ data }}


content 'multi':
"global section"
import example
^L
"per-hit section"
data = "foo"
^L text/plain
{{ data }}
^L text/html
HTML {{ data }}
^L application/json
{ 'json': '{{ data }}' }

"""

import copy 

from aspen import Response
from aspen.resources.dynamic_resource import DynamicResource
from aspen._tornado.template import Template


class NegotiatedResource(DynamicResource):
    """This is a negotiated resource. It has three or more pages
    """

    min_pages = 3
    max_pages = 99

    def compile_page(self, page, padding):
        """Given a bytestring, return a Template instance.

        This method depends on fs and website attributes on self.
        
        We used to take advantage of padding, but:

            a) Tornado templates have some weird error handling that we haven't
            exposed yet.
            
            b) It's counter-intuitive if your template resources show up in the
            browser with tons of whitespace at the beginning of them.

        """
	if '\n' in page:
            # use the specified specline
            specline, input = page.split('\n',1)
        else:
            # no specline specifed - default to the default media type
            specline, input = self.website.media_type_default, page
        specline = specline.strip()
        print "specline: " + repr(specline)
        return (specline,
                Template( input
                       , name = self.fs
                       , loader = self.website.template_loader 
                       , compress_whitespace = False
                        )
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


    def get_response(self, namespace):
        """Given a namespace dict, return a response object.
        """
        request = namespace['request']
        accepts = request.headers.get('Accept')
        if accepts:
            available_types = [ t for t, p in self.pages ] # order is important!
            r_type = mimetypes.best_match(available_types, accepts)
            responder = dict(self.pages)[r_type]
        else:
            r_type, responder = self.pages[0]

        response = namespace['response']
        response.body = responder.generate(**namespace)
        if response.headers.get('Content-Type') is None:
            response.headers['Content-Type'] = r_type
        return response

