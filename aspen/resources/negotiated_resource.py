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

from aspen._mimeparse import mimeparse
from aspen.resources.dynamic_resource import DynamicResource


PAGE_BREAK = chr(12)
renderer_re = re.compile(r'#![a-z0-9.-]+')
media_type_re = re.compile(r'[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+')


class NegotiatedResource(DynamicResource):
    """This is a negotiated resource. It has three or more pages
    """

    min_pages = 3
    max_pages = None

    def compile_page(self, page, padding):
        """Given a bytestring, return a (type, renderer) pair """

        # parse specline
        if '\n' in page:
            # use the specified specline
            specline, raw = page.split('\n',1)
        else:
            # no specline specifed - default to the default media type
            specline, raw = self.website.media_type_default, page
            specline = specline.encode('US-ASCII') # XXX hack, rethink defaults
        specline = specline.strip()

        # hydrate
        renderer, media_type = self._parse_specline(specline)
        if renderer is None:
            renderer = "tornado" # XXX hack, compute from media type
        assert media_type is not None, media_type
        renderer = self.website.renderer_factories[renderer]
        render = renderer(self.fs, raw)

        return (media_type, render)


    def _parse_specline(self, line):
        """Given a bytestring, return a two-tuple.

        The incoming string is expected to be of the form:

            ^L #!renderer media/type
       
        The renderer is optional. It will be computed based on media type if
        absent. The return two-tuple contains None or a unicode for each part.
        SyntaxError is raised if there aren't one or two parts or if either of
        the parts is malformed. If only one part is passed in it's interpreted
        as a media type.
        
        """
        assert isinstance(line, str), type(line)

        # Parse into one or two parts.
        line = line.strip('\n ' + PAGE_BREAK)
        parts = line.split()
        nparts = len(parts)
        if nparts not in (1, 2):
            raise SyntaxError("A negotiated simplate specline must have one "
                              "or two parts: #!renderer media/type. Yours is: "
                              "%s." % line)
       
        # Assign parts.
        renderer = None
        if nparts == 1:
            media_type = parts[0]
        else:
            assert nparts == 2, nparts
            renderer, media_type = parts

        # Validate renderer.
        if renderer is not None:
            if renderer_re.match(renderer) is None:
                msg = "Malformed renderer %s in specline %s. It must match %s."
                raise SyntaxError(msg % (renderer, line, renderer_re.pattern))
            renderer = renderer[2:]  # strip off the hashbang 
            renderer = renderer.decode('US-ASCII')

        # Validate media type.
        if media_type_re.match(media_type) is None:
            msg = ("Malformed media type %s in specline %s. It must match "
                   "%s.")
            msg %= (media_type, line, media_type_re.pattern)
            raise SyntaxError(msg)
        media_type = media_type.decode('US-ASCII')

        # Return.
        return renderer, media_type


    def get_response(self, context):
        """Given a namespace dict, return a response object.
        """
        request = context['request']
        accepts = request.headers.get('Accept')
        if accepts:
            available_types = [ t for t, p in self.pages ] # order is important!
            media_type = mimeparse.best_match(available_types, accepts)
            render = dict(self.pages)[media_type]
        else:
            media_type, render = self.pages[0]

        response = context['response']
        response.body = render(context)
        if response.headers.get('Content-Type') is None:
            response.headers['Content-Type'] = media_type
        return response

