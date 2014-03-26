"""
aspen.resources.negotiated_resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implements negotiated resources.

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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import sys

from aspen import Response, log
import mimeparse
from aspen.resources.dynamic_resource import DynamicResource
from aspen.resources.pagination import parse_specline

renderer_re = re.compile(r'[a-z0-9.-_]+$')
media_type_re = re.compile(r'[A-Za-z0-9.+*-]+/[A-Za-z0-9.+*-]+$')


class NegotiatedResource(DynamicResource):
    """This is a negotiated resource. It has three or more pages.
    """

    min_pages = 3
    max_pages = None


    def __init__(self, *a, **kw):
        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        DynamicResource.__init__(self, *a, **kw)


    def compile_page(self, page):
        """Given a bytestring, return a (renderer, media type) pair.
        """
        make_renderer, media_type = self._parse_specline(page.header)
        renderer = make_renderer(self.fs, page.content)
        if media_type in self.renderers:
            raise SyntaxError("Two content pages defined for %s." % media_type)

        # update internal data structures
        self.renderers[media_type] = renderer

        self.available_types.append(media_type)

        return (renderer, media_type)  # back to parent class

    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        request = context['request']

        # find an Accept header
        accept = request.headers.get('X-Aspen-Accept', None)
        if accept is not None:      # indirect negotiation
            failure = Response(404)
        else:                       # direct negotiation
            accept = request.headers.get('Accept', None)
            msg = "The following media types are available: %s."
            msg %= ', '.join(self.available_types)
            failure = Response(406, msg.encode('US-ASCII'))

        # negotiate or punt
        render, media_type = self.pages[2]  # default to first content page
        if accept is not None:
            try:
                media_type = mimeparse.best_match(self.available_types, accept)
            except:
                # exception means don't override the defaults
                log("Problem with mimeparse.best_match(%r, %r): %r " % (self.available_types, accept, sys.exc_info()))
            else:
                if media_type == '':    # breakdown in negotiations
                    raise failure
                del failure
                render = self.renderers[media_type] # KeyError is a bug

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

            media_type via renderer

        The renderer is optional. It will be computed based on media type if
        absent. The return two-tuple contains a render function and a media
        type (as unicode). SyntaxError is raised if there aren't one or two
        parts or if either of the parts is malformed. If only one part is
        passed in it's interpreted as a media type.

        """
        # Parse into parts
        parts = parse_specline(specline)

        #Assign parts
        media_type, renderer = parts
        if renderer == '':
            renderer = self.website.default_renderers_by_media_type[media_type]

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
        if renderer_re.match(renderer) is None:
            possible =', '.join(sorted(self.website.renderer_factories.keys()))
            msg = ("Malformed renderer %s. It must match %s. Possible "
                   "renderers (might need third-party libs): %s.")
            raise SyntaxError(msg % (renderer, renderer_re.pattern, possible))

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
