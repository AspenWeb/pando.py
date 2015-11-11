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

from .backcompat import StringIO
from .pagination import split_and_escape, parse_specline, Page

renderer_re = re.compile(r'[a-z0-9.-_]+$')
media_type_re = re.compile(r'[A-Za-z0-9.+*-]+/[A-Za-z0-9.+*-]+$')

MIN_PAGES=2
MAX_PAGES=None


def _ordinal(n):
    ords = [ 'zero' , 'one' , 'two', 'three', 'four'
           , 'five', 'six', 'seven', 'eight', 'nine' ]
    if 0 <= n < len(ords):
        return ords[n]
    return str(n)


def _decode(raw):
    """As per PEP 263, decode raw data according to the encoding specified in
       the first couple lines of the data, or in ASCII.  Non-ASCII data without
       an encoding specified will cause UnicodeDecodeError to be raised.
    """
    assert type(raw) is (bytes if sys.version_info[0] == 3 else str)  # sanity check

    decl_re = re.compile(r'^[ \t\f]*#.*coding[:=][ \t]*([-\w.]+)')

    def get_declaration(line):
        match = decl_re.match(line)
        if match:
            return match.group(1)
        return None

    encoding = None
    fulltext = b''
    sio = StringIO(raw)
    for line in (sio.readline(), sio.readline()):
        potential = get_declaration(line)
        if potential is not None:
            if encoding is None:

                # If both lines match, use the first. This matches Python's
                # observed behavior.

                encoding = potential
                munged = b'# encoding set to {0}\n'.format(encoding)

            else:

                # But always munge any encoding line. We can't simply remove
                # the line, because we want to preserve the line numbering.
                # However, later on when we ask Python to exec a unicode
                # object, we'll get a SyntaxError if we have a well-formed
                # `coding: # ` line in it.

                munged = b'# encoding NOT set to {0}\n'.format(potential)

            line = line.split(b'#')[0] + munged

        fulltext += line
    fulltext += sio.read()
    sio.close()
    return fulltext.decode(encoding or b'ascii')


class SimplateException(Exception):
    def __init__(self, available_types):
        self.available_types = available_types


class SimplateDefaults(object):
    def __init__(self, renderers_by_media_type, renderer_factories, initial_context):
        """
        Things that are usually the same across all simplates:

        renderers_by_media_type - dict[media_type_name] -> renderer_name
        renderer_factories - dict[renderer_name] -> renderer_factory
        initial_context - initial context passed into the 'run-once' page
        """
        self.renderers_by_media_type = renderers_by_media_type # type: Dict[str, str]
        self.renderer_factories = renderer_factories           # type: Dict[str, Callable]
        self.initial_context = initial_context                 # type: Dict[str, object]


class Simplate(object):
    """A simplate is a dynamic resource with multiple syntaxes in one file.
    """

    def __init__(self, defaults, fs, raw, default_media_type):
        """Instantiate a simplate.

        defaults - a SimplateDefaults object
        fs - path to this simplate
        raw - raw content of this simplate as bytes
        decoded - content of this simplate as unicode
        default_media_type - the default content_type of this simplate
        """

        self.defaults = defaults                      # type: SimplateDefaults
        self.fs = fs                                  # type: str
        self.raw = raw                                # type: str
        self.decoded = _decode(raw)                   # type: unicode
        self.default_media_type = default_media_type  # type: str

        self.renderers = {}         # mapping of media type to render function
        self.available_types = []   # ordered sequence of media types
        pages = self.parse_into_pages(self.decoded)
        self.pages = self.compile_pages(pages)


    def best_match(self, accept, default=None):
        """
        get the media type provided by this simplate that best matches
        the supplied Accept: header, or the default type (that of the
        first template page) if no accept header is provided (is None),
        or raise SimplateException if no matches are available
        to a valid Accept: header.

        This is what the simplate will call internally to determine
        which template to use.
        """
        _, media_type = self.pages[2]  # default to first content page
        if accept is None:
            # No accept header provided, use the default
            return media_type
        media_type = mimeparse.best_match(self.available_types, accept)
        if media_type == '':    # breakdown in negotiations
            raise SimplateException(self.available_types)
        return media_type


    def respond(self, accept, context):
        """
        get the response to a request for this page

        accept - an HTTP Accept: header asking for this page
        context - a dict of execution context values you wish to supply
                  * Note that these are overriden by values that are carried
                  over from the execution of the zeroth page
        """

        # copy the state dict to avoid accidentally mutating it
        context = dict(context)
        # override it with values from the first page
        context.update(self.pages[0])
        # use this as the context to execute the second page in
        exec(self.pages[1], context)

        if '__all__' in context:
            # templates will only see variables named in __all__
            context = dict([ (k, context[k]) for k in context['__all__'] ])

        # find matching media type
        media_type = self.best_match(accept)
        # load that renderer
        render = self.renderers[media_type]
        # render it
        body = render(context)

        return media_type, body


    def parse_into_pages(self, decoded):
        """Given a bytestring that is the entire simplate, return a list of pages.

        If there's one page, it's a template.
        If there's more than one page, the first page is always python and the last is always a template.
        If there's more than two pages, the second page is python _unless it has a specline_, which makes it a template

        """

        pages = list(split_and_escape(decoded))
        npages = len(pages)
        blank = [ Page(b'') ]

        if npages == 1:
            pages = blank + blank + pages
        elif npages == 2:
            pages = blank + pages
        elif pages[1].header: # it's got a header, so it's a template
            pages = blank + pages

        return pages


    def compile_pages(self, pages):
        """Given a list of pages, replace the pages with objects.

        Page 0 is the 'run once' page - it is executed and the resulting
            context stored in self.pages[0]
        Page 1 is the 'run every' page - it is compiled for easier execution
            later, and stored in self.pages[1]
        Subsequent pages are templates, so each one's content_type and
            respective renderer are stored as a tuple in self.pages[n]
        """

        # Exec the first page and compile the second.
        # ===========================================

        one, two = pages[:2]

        context = dict()
        context['__file__'] = self.fs
        context.update(self.defaults.initial_context)

        one = compile(one.padded_content, self.fs, 'exec')
        exec one in context    # mutate context
        one = context          # store it

        two = compile(two.padded_content, self.fs, 'exec')

        pages[:2] = (one, two)
        pages[2:] = (self.compile_page(page) for page in pages[2:])

        return pages


    def compile_page(self, page):
        """Given a Page, return a (renderer, media type) pair.
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

        Both are optional.

        The media_type will default to the default_media_type supplied to
        this simplate at instantiation time.  (Possibly determined by a
        file extension or other metadata)

        The renderer will be computed based on media type if absent.

        The return two-tuple contains a render function and a media
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
