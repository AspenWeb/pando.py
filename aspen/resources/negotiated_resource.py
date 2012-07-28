"""Implements negotiated resources.

Aspen supports content negotiation. If a file has no file extension, then it
will be handled as a "negotiated resource". The format of the file is like
this:

    import foo, json
    ^L
    data = foo.bar(request)
    ^L text/plain
    {{ data }}
    ^L text/json
    {{ json.dumps(data) }}

We have vendored in Joe Gregorio's content negotiation library to do the heavy
lifting (parallel to how we handle _cherrypy and _tornado vendoring). If a file
*does* have a file extension (foo.html), then it is a rendered resource with a
mimetype computed from the file extension. It is a SyntaxError for a file to
have both an extension *and* multiple content pages.

"""
import re

from aspen import Response
from aspen._mimeparse import mimeparse
from aspen.resources import PAGE_BREAK
from aspen.resources.dynamic_resource import DynamicResource
from aspen.utils import typecheck


renderer_re = re.compile(r'#![a-z0-9.-]+')
media_type_re = re.compile(r'[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+')


class NegotiatedResource(DynamicResource):
    """This is a negotiated resource. It has three or more pages.
    """

    min_pages = 3
    max_pages = None


    def __init__(self, *a, **kw):
        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        DynamicResource.__init__(self, *a, **kw)


    def compile_page(self, page, __ignored):
        """Given a bytestring, return a (renderer, media type) pair.
        """
        if '\n' in page:
            specline, raw = page.split('\n', 1)
        else:
            specline = ''
            raw = page
        specline = specline.strip(PAGE_BREAK + ' \n')
        make_renderer, media_type = self._parse_specline(specline)
        render = make_renderer(self.fs, raw)
        if media_type in self.renderers:
            raise SyntaxError("Two content pages defined for %s." % media_type)

        # update internal data structures
        self.renderers[media_type] = render
        self.available_types.append(media_type)

        return (render, media_type)  # back to parent class


    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        request = context['request']

        # find an Accept header
        accept = request.headers.get('X-Aspen-Accept', None)
        if accept is not None:      # indirect negotiation
            failure = 404
        else:                       # direct negotiation
            accept = request.headers.get('Accept', None)
            failure = 406

        # negotiate or punt
        if accept is not None:
            media_type = mimeparse.best_match(self.available_types, accept)
            if media_type == '':    # breakdown in negotiations
                if failure == 404:
                    failure = Response(404)
                elif failure == 406:
                    msg = "The following media types are available: %s."
                    msg %= ', '.join(self.available_types)
                    failure = Response(406, msg.encode('US-ASCII'))
                raise failure
            render = self.renderers[media_type] # KeyError is a bug
        else:  # punt
            render, media_type = self.pages[2]  # default to first content page

        response = context['response']
        response.body = render(context)
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = media_type
            if media_type.startswith('text/'):
                charset = response.charset
                if charset is not None:
                    response.headers['Content-Type'] += '; charset=' + charset

        return response


    def _parse_specline(self, specline):
        """Given a bytestring, return a two-tuple.

        The incoming string is expected to be of the form:

            ^L #!renderer media/type

        The renderer is optional. It will be computed based on media type if
        absent. The return two-tuple contains a render function and a media
        type (as unicode). SyntaxError is raised if there aren't one or two
        parts or if either of the parts is malformed. If only one part is
        passed in it's interpreted as a media type.

        """
        typecheck(specline, str)
        if specline == "":
            raise SyntaxError("Content pages in negotiated resources must "
                              "have a specline.")

        # Parse into one or two parts.
        parts = specline.split()
        nparts = len(parts)
        if nparts not in (1, 2):
            raise SyntaxError("A negotiated resource specline must have one "
                              "or two parts: #!renderer media/type. Yours is: "
                              "%s." % specline)

        # Assign parts.
        if nparts == 1:
            media_type = parts[0]
            renderer = self.website.default_renderers_by_media_type[media_type]
            renderer = "#!" + renderer
        else:
            assert nparts == 2, nparts
            renderer, media_type = parts

        # Validate media type.
        if media_type_re.match(media_type) is None:
            msg = ("Malformed media type %s in specline %s. It must match "
                   "%s.")
            msg %= (media_type, specline, media_type_re.pattern)
            raise SyntaxError(msg)

        # Hydrate and validate renderer.
        make_renderer = self._get_renderer_factory(media_type, renderer)

        # Return.
        return (make_renderer, media_type)


    def _get_renderer_factory(self, media_type, renderer):
        """Given two bytestrings, return a renderer factory or None.
        """
        typecheck(media_type, str, renderer, str)
        if renderer_re.match(renderer) is None:
            possible =', '.join(sorted(self.website.renderer_factories.keys()))
            msg = ("Malformed renderer %s. It must match %s. Possible "
                   "renderers (might need third-party libs): %s.")
            raise SyntaxError(msg % (renderer, renderer_re.pattern, possible))
        renderer = renderer[2:]  # strip off the hashbang
        renderer = renderer.decode('US-ASCII')

        factories = self.website.renderer_factories
        make_renderer = factories.get(renderer, None)
        if isinstance(make_renderer, ImportError):
            raise make_renderer
        elif make_renderer is None:
            possible = []
            want_legend = False
            for k, v in sorted(factories.iteritems()):
                if isinstance(v, ImportError):
                    k = '*' + k
                    want_legend = True
                possible.append(k)
            possible = ', '.join(possible)
            if want_legend:
                legend = " (starred are missing third-party libraries)"
            else:
                legend = ''
            raise ValueError("Unknown renderer for %s: %s. Possible "
                             "renderers%s: %s."
                             % (media_type, renderer, legend, possible))
        return make_renderer
