"""Negotiated resources.

Aspen supports multiplexing content types on a single HTTP endpoint via content
negotiation. If a file has no file extension, then it will be handled as a
"negotiated resource".  The format of the file is like this:

    import foo, json
    ^L
    data = foo.bar(request)
    ^L text/plain
    {{ data }}
    ^L text/json
    {{ json.dumps(data) }}

We have vendored in Joe Gregorio's content negotiation library to do the heavy
lifting (parallel to how we handle _cherrypy and _tornado vendoring).

If a file *does* have a file extension (foo.html), then it is a template
resource with a mimetype computed from the file extension. It is a SyntaxError
for a file to have both an extension *and* multiple content pages.

"""
from aspen.resources.dynamic_resource import DynamicResource


PAGE_BREAK = chr(12)


class NegotiatedResource(DynamicResource):
    """This is a negotiated resource. It has three or more pages
    """

    min_pages = 3
    max_pages = None

    def compile_page(self, page, padding):
        """Given a bytestring, return a (type, renderer) pair """
        if '\n' in page:
            # use the specified specline
            specline, input = page.split('\n',1)
        else:
            # no specline specifed - default to the default media type
            specline, input = self.website.media_type_default, page
        specline = specline.strip()

        # figure out which type this is and which renderer to use
        renderer_name, content_type = self._parse_specline(specline)
        if renderer_name is None:
            renderer_name = self.website.template_loader_default
        if content_type is None:
            content_type = self.website.media_type_default

        # get the render engine
        renderer = self.website.template_loaders[renderer_name]

        # return a tuple of (content_type,  page render function)
        template_root = self.website.project_root or self.website.www_root
        return (content_type, renderer( template_root, self.fs, input ))


    def _parse_specline(self, line):
        """parse out the specline 

            ^L #!renderer content/type
        
            return None for any parts unspecified on the specline
        """
        # TODO: enforce order
        line = line.strip('\n ' + PAGE_BREAK)
        renderer, content_type = None, None
        for arg in line.split(' '):
            if arg.startswith('#!'):
                renderer = arg[2:]
            elif arg:
                content_type = arg
        return renderer, content_type


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
        response.body = responder(**namespace)
        if response.headers.get('Content-Type') is None:
            response.headers['Content-Type'] = r_type
        return response

