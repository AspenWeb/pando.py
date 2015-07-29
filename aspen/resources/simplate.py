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
from .. import Response, log
from .pagination import split_and_escape, parse_specline
from .resource import Resource


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

MIN_PAGES=3
MAX_PAGES=None

class Simplate(Resource):
    """A simplate is a dynamic resource with multiple syntaxes in one file.
    """

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)

        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        pages = self.parse_into_pages(self.raw)
        self.pages = self.compile_pages(pages)


    def respond(self, state):
        state.setdefault('response', Response(charset=self.website.charset_dynamic))
        spt_context = dict(state, **self.pages[0])  # copy the state dict to avoid accidentally
        exec(self.pages[1], spt_context)            #  mutating it

        if '__all__' in spt_context:
            # templates will only see variables named in __all__
            spt_context = dict([ (k, spt_context[k]) for k in spt_context['__all__'] ])

        return self.get_response(state, spt_context)


    def parse_into_pages(self, raw):
        """Given a bytestring and a boolean, return a list of pages.
        """

        pages = list(split_and_escape(raw))
        npages = len(pages)

        # Check for too few pages.
        if npages < MIN_PAGES:
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have at least %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[MIN_PAGES]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

        # Check for too many pages. This is user error.
        if MAX_PAGES is not None and npages > MAX_PAGES:
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have at most %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[MAX_PAGES]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

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
        make_renderer, media_type = self._unbound_parse_specline(page.header)
        renderer = make_renderer(self.fs, page.content, media_type, page.offset)
        if media_type in self.renderers:
            raise SyntaxError("Two content pages defined for %s." % media_type)

        # update internal data structures
        self.renderers[media_type] = renderer
        self.available_types.append(media_type)

        return (renderer, media_type)  # back to parent class


    def get_response(self, state, spt_context):
        """Given two context dicts, return a response object.
        """
        dispatch_result = state['dispatch_result']

        # find an Accept header
        accept = dispatch_result.extra.get('accept', None)
        if accept is not None:      # indirect negotiation
            failure = Response(404)
        else:                       # direct negotiation
            accept = state.get('accept_header')
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
                log( "Problem with mimeparse.best_match(%r, %r): %r "
                   % (self.available_types, accept, sys.exc_info())
                    )
            else:
                if media_type == '':    # breakdown in negotiations
                    raise failure
                del failure
                render = self.renderers[media_type] # KeyError is a bug

        response = state['response']
        response.body = render(spt_context)
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = media_type
            if media_type.startswith('text/'):
                charset = response.charset
                if charset is not None:
                    response.headers['Content-Type'] += '; charset=' + charset

        return response


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
        media_type, renderer = parse_specline(specline)

        if media_type == '':
            # no media type specified, use the default
            media_type = self.media_type
        if renderer == '':
            # no renderer specified, use the default
            renderer = self.website.default_renderers_by_media_type[media_type]

        # Validate media type.
        if media_type_re.match(media_type) is None:
            msg = ("Malformed media type '%s' in specline '%s'. It must match "
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
