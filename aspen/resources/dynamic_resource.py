from aspen import Response
from aspen.resources import PAGE_BREAK
from aspen.resources.resource import Resource


class StringDefaultingList(list):
    def __getitem__(self, key):
        try:
            return list.__getitem__(self, key)
        except KeyError:
            return str(key)

ORDINALS = StringDefaultingList([ 'zero' , 'one' , 'two', 'three', 'four'
                                , 'five', 'six', 'seven', 'eight', 'nine'
                                 ])


class DynamicResource(Resource):
    """This is the base for JSON, negotiating, socket, and rendered resources.
    """

    min_pages = None  # set on subclass
    max_pages = None

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)
        self.pages = self.parse_into_pages(self.raw)
        self.pages = self.compile_pages(self.pages)


    def respond(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response(charset=self.website.charset_dynamic)


        # Populate context.
        # =================

        context = self.populate_context(request, response)


        # Exec page two.
        # ==============

        try:
            exec self.pages[1] in context
        except Response, response:
            response = self.process_raised_response(response)
            raise response


        # Hook.
        # =====

        try:
            response = self.get_response(context)
        except Response, response:
            response = self.process_raised_response(response)
            raise response
        else:
            return response


    def populate_context(self, request, response):
        """Factored out to support testing.
        """
        context = request.context
        context.update(self.pages[0])
        context['request'] = request
        context['response'] = response
        context['resource'] = self
        return context


    def parse_into_pages(self, raw):
        """Given a bytestring, return a list of pages.

        Subclasses extend this to implement additional semantics.

        """

        # Support caret-L in addition to .
        uncareted = raw.replace("^L", PAGE_BREAK)
        pages = uncareted.split(PAGE_BREAK)
        npages = len(pages)

        # Check for too few pages. This is a sanity check as get_resource_class
        # should guarantee this. Bug if it fails.
        assert npages >= self.min_pages, npages

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

        return pages


    def compile_pages(self, pages):
        """Given a list of bytestrings, replace the bytestrings with objects.

        All dynamic resources compile the first two pages the same way. It's
        the third and following pages that differ, so we require subclasses to
        supply a method for that: compile_page.

        """

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier. In
        # general it's nice to standardize this, I think. XXX Should we be
        # going back to \r\n for the wire? That's HTTP, right?

        for i, page in enumerate(pages):
            pages[i] = page.replace('\r\n', '\n')

        one = pages[0]
        two = pages[1]


        # Compute paddings and pad the second and third pages.
        # ====================================================
        # This is so we get accurate tracebacks. We pass padding to the
        # compile_page hook; the SocketResource subclass uses it, since it has
        # an additional logic page that it wants to pad. We don't simply pad
        # all pages because then for content pages the user would view source
        # in their browser and see nothing but whitespace until they scroll way
        # down.

        paddings = self._compute_paddings(pages)
        two = paddings[1] + two


        # Exec the first page and compile the second.
        # ===========================================

        context = dict()
        context['__file__'] = self.fs
        context['website'] = self.website

        one = compile(one, self.fs, 'exec')
        exec one in context    # mutate context
        one = context          # store it

        two = compile(two, self.fs, 'exec')

        pages[0] = one
        pages[1] = two


        # Subclasses are responsible for the rest.
        # ========================================

        for i, page in enumerate(pages[2:]):
            i += 2  # no start kw to enumerate in Python 2.5
            pages[i] = self.compile_page(page, paddings[i])

        return pages


    def _compute_paddings(pages):
        """Given a list of bytestrings, return a 1-shorter list of bytestrings.
        """
        if not pages:
            return []

        # A file with many, many lines would flog this algorithm.
        lines_in = lambda s: '\n' * s.count('\n')
        paddings = ['']  # first page doesn't need padding
        paddings += [paddings[-1] + lines_in(page) for page in pages[:-1]]
        return paddings

    _compute_paddings = staticmethod(_compute_paddings)


    # Hooks
    # =====

    def compile_page(self, *a):
        """Given a bytestring, return an object.
        """
        raise NotImplementedError

    def process_raised_response(self, response):
        """Given a response object, return a response object.
        """
        return response

    def get_response(self, context):
        """Given a context dictionary, return a Response object.
        """
        raise NotImplementedError
