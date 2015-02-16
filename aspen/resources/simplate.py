"""
aspen.resources.dynamic_resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import sys

import mimeparse
from aspen import Response, log
from aspen.resources.pagination import split_and_escape, Page, parse_specline
from aspen.resources.resource import Resource


renderer_re = re.compile(r'[a-z0-9.-_]+$')
media_type_re = re.compile(r'[A-Za-z0-9.+*-]+/[A-Za-z0-9.+*-]+$')


class StringDefaultingList(list):
    def __getitem__(self, key):
        try:
            return list.__getitem__(self, key)
        except KeyError:
            return str(key)

ORDINALS = StringDefaultingList([ 'zero' , 'one' , 'two', 'three', 'four'
                                , 'five', 'six', 'seven', 'eight', 'nine'
                                 ])


class Simplate(Resource):
    """A simplate is a dynamic resource with multiple syntaxes in one file.
    """

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)

        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        self.min_pages, self.max_pages = (1, 4) if self.is_bound else (3, None)

        pages = self.parse_into_pages(self.raw, self.is_bound)
        self.pages = self.compile_pages(pages)


    def respond(self, context):
        context.update(self.pages[0])
        response = context.get('response')
        if response is None:
            response = Response(charset=self.website.charset_dynamic)
        context['response'] = response

        exec self.pages[1] in context

        # if __all__ is defined, only pass those variables to templates
        # if __all__ is not defined, pass full context to templates

        if '__all__' in context:
            newcontext = dict([ (k, context[k]) for k in context['__all__'] ])
            context = newcontext

        response = self.get_response(context)
        return response


    def parse_into_pages(self, raw, is_bound):
        """Given a bytestring and a boolean, return a list of pages.
        """

        pages = list(split_and_escape(raw))
        npages = len(pages)

        # Check for too few pages.
        if npages < self.min_pages:
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have at least %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[self.min_pages]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

        # Check for too many pages. This is user error.
        if self.max_pages is not None and npages > self.max_pages:
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have at most %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[self.max_pages]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

        # Pad front with empty pages for bound simplates.
        if is_bound:
            num_extra_pages = 3 - len(pages)
            # Note that range(x) returns an empty list if x < 1
            pages[0:0] = (Page('') for _ in range(num_extra_pages))

        return pages


    def compile_pages(self, pages):
        """Given a list of pages, replace the pages with objects.

        All dynamic resources compile the first two pages the same way. It's
        the third and following pages that differ, so we require subclasses to
        supply a method for that: compile_page.

        """

        # Exec the first page and compile the second.
        # ===========================================

        one, two = pages[:2]

        context = dict()
        context['__file__'] = self.fs
        context['website'] = self.website

        one = compile(one.padded_content, self.fs, 'exec')
        exec one in context    # mutate context
        one = context          # store it

        two = compile(two.padded_content, self.fs, 'exec')

        pages[:2] = (one, two)
        pages[2:] = (self.compile_page(page) for page in pages[2:])

        return pages


    def compile_page(self, page):
        """Given a bytestring, return a (renderer, media type) pair.
        """
        _parse_specline = self._bound_parse_specline \
                            if self.is_bound else self._unbound_parse_specline
        make_renderer, media_type = _parse_specline(page.header)
        renderer = make_renderer(self.fs, page.content, media_type, page.offset)
        if media_type in self.renderers:
            raise SyntaxError("Two content pages defined for %s." % media_type)

        # update internal data structures
        self.renderers[media_type] = renderer
        self.available_types.append(media_type)

        return (renderer, media_type)  # back to parent class


    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        dispatch_result = context['dispatch_result']

        # find an Accept header
        accept = dispatch_result.extra.get('accept', None)
        if accept is not None:      # indirect negotiation
            failure = Response(404)
        else:                       # direct negotiation
            accept = context.get('accept_header')
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


    def _bound_parse_specline(self, specline):
        """Parse specline for bound simplate.

        Bound simplates have a simpler specline than unbound simplates. They
        don't have a media type, and the renderer is optional.

        """
        #parse into parts.
        parts = parse_specline(specline)

        #Assign parts, discard media type
        renderer = parts[1]
        media_type = self.media_type
        if not renderer:
            renderer = self.website.default_renderers_by_media_type[media_type]

        #Hydrate and validate renderer
        make_renderer = self._get_renderer_factory(media_type, renderer)

        return (make_renderer, media_type)


    def _unbound_parse_specline(self, specline):
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
            legend = ''
            for k, v in sorted(factories.iteritems()):
                if isinstance(v, ImportError):
                    k = '*' + k
                    legend = " (starred are missing third-party libraries)"
                possible.append(k)
            possible = ', '.join(possible)
            raise ValueError("Unknown renderer for %s: %s. Possible "
                             "renderers%s: %s."
                             % (media_type, renderer, legend, possible))
        return make_renderer
