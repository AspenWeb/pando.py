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
import re
from aspen.resources.dynamic_resource import DynamicResource


PAGE_BREAK = chr(12)
renderer_re = re.compile(r'#![a-z_]+')
media_type_re = re.compile(r'[a-z]+/[a-z]+')


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
        """Given a bytestring, return a two-tuple.

        The incoming string is expected to be of the form:

            ^L #!renderer media/type
       
        Either part is optional but there must be at least one part. The return
        two-tuple contains None or a bytestring for each part. SyntaxError is
        raised if there aren't one or two parts or if either of the parts is
        malformed. If only one part is passed it's interpreted as a renderer if
        it starts with a hashbang, media type otherwise.
        
        """
        line = line.strip('\n ' + PAGE_BREAK)
        renderer, media_type = None, None
        parts = line.split()
        nparts = len(parts)
        if nparts not in (1, 2):
            raise SyntaxError("A negotiated resource specline must have one "
                              "or two parts: #!renderer media/type. Yours is: "
                              "%s." % line)
        if nparts == 1:
            arg = parts[0]
            if arg.startswith('#!'):
                renderer = arg
            else:
                media_type = arg
        else:
            assert nparts == 2, nparts
            renderer, media_type = parts

        if renderer is not None:
            if renderer_re.match(renderer) is None:
                raise SyntaxError("Malformed renderer %s in specline %s." 
                                  % (renderer, line))
            renderer = renderer[2:]  # strip off the hashbang 
        if media_type is not None:
            if media_type_re.match(media_type) is None:
                raise SyntaxError("Malformed media_type %s in specline %s." 
                                  % (media_type, line))

        return renderer, media_type


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

