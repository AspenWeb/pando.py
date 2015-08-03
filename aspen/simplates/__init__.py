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

from .. import log
from .pagination import split_and_escape, parse_specline

renderer_re = re.compile(r'[a-z0-9.-_]+$')
media_type_re = re.compile(r'[A-Za-z0-9.+*-]+/[A-Za-z0-9.+*-]+$')

MIN_PAGES=3
MAX_PAGES=None


def _ordinal(n):
    ords = [ 'zero' , 'one' , 'two', 'three', 'four'
           , 'five', 'six', 'seven', 'eight', 'nine' ]
    if 0 <= n < len(ords):
        return ords[n]
    return str(n)


class SimplateException(Exception):
    def __init__(self, available_types):
        self.available_types = available_types


class SimplateDefaults(object):
    def __init__(self, renderers_by_media_type, renderer_factories):
        """
        renderers_by_media_type - dict[str(media_type_name)] -> str(renderer_name)
        renderer_factories - dict[str(renderer_name)] -> func(renderer_factory)
        """
        self.renderers_by_media_type = renderers_by_media_type
        self.renderer_factories = renderer_factories


class Simplate(object):
    """A simplate is a dynamic resource with multiple syntaxes in one file.
    """

    def __init__(self, defaults, website, fs, raw, default_media_type):
        self.defaults = defaults
        self.website = website
        self.fs = fs
        self.raw = raw
        self.default_media_type = default_media_type

        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        pages = self.parse_into_pages(self.raw)
        self.pages = self.compile_pages(pages)


    def respond(self, state):
        # copy the state dict to avoid accidentally mutating it
        spt_context = dict(state)
        # override it with values from the first page
        spt_context.update(self.pages[0])
        # use this as the context to execute the second page in
        exec(self.pages[1], spt_context)

        if '__all__' in spt_context:
            # templates will only see variables named in __all__
            spt_context = dict([ (k, spt_context[k]) for k in spt_context['__all__'] ])

        return self.get_response(state, spt_context)


    def get_response(self, state, spt_context):
        """Given two context dicts, return a response object.
        """

        accept = state['dispatch_result'].extra.get('accept')
        if accept is None:
            accept = state.get('accept_header')

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
                    raise SimplateException(self.available_types)
                render = self.renderers[media_type] # KeyError is a bug

        body = render(spt_context)
        response = state['response']
        response.body = body
        if 'Content-Type' not in response.headers:
            if media_type.startswith('text/') and response.charset is not None:
                media_type += '; charset=' + response.charset
            response.headers['Content-Type'] = media_type

        return response


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
                   , _ordinal(MIN_PAGES)
                   , self.fs
                   , _ordinal(npages)
                    )
            raise SyntaxError(msg)

        # Check for too many pages. This is user error.
        if MAX_PAGES is not None and npages > MAX_PAGES:
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have at most %s pages; %s has %s."
            msg %= ( type_name
                   , _ordinal[MAX_PAGES]
                   , self.fs
                   , _ordinal[npages]
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
        make_renderer, media_type = self._parse_specline(page.header)
        renderer = make_renderer(self.fs, page.content, media_type, page.offset)
        if media_type in self.renderers:
            raise SyntaxError("Two content pages defined for %s." % media_type)

        # update internal data structures
        self.renderers[media_type] = renderer
        self.available_types.append(media_type)

        return (renderer, media_type)  # back to parent class

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
        media_type, renderer = parse_specline(specline)

        if media_type == '':
            # no media type specified, use the default
            media_type = self.default_media_type
        if renderer == '':
            # no renderer specified, use the default
            renderer = self.defaults.renderers_by_media_type[media_type]

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
        factories = self.defaults.renderer_factories
        if renderer_re.match(renderer) is None:
            possible =', '.join(sorted(factories.keys()))
            msg = ("Malformed renderer %s. It must match %s. Possible "
                   "renderers (might need third-party libs): %s.")
            raise SyntaxError(msg % (renderer, renderer_re.pattern, possible))

        renderer = renderer.decode('US-ASCII')

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
