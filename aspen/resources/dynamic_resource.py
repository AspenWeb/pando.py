from aspen import Response
from aspen.resources.resource import Resource


PAGE_BREAK = chr(12)

# Global page limits. There are further limits per-resource-type.
MIN_PAGES = 2
MAX_PAGES = 99

class StringDefaultingList(list):
    def __getitem__(self, key):
        try:
            return super(StringDefaultingList, self).__getitem__(key)
        except KeyError:
            return str(key)
ORDINALS = StringDefaultingList([ 'zero' , 'one' , 'two', 'three', 'four'
                                , 'five', 'six', 'seven', 'eight', 'nine'])


class DynamicResource(Resource):
    """This is a base class for json, socket, and template resources.
    """

    min_pages = None # set on subclass
    max_pages = None
    
    def __init__(self, *a, **kw):
        if self.max_pages:
            assert MIN_PAGES <= self.max_pages <= MAX_PAGES # sanity check
        super(DynamicResource, self).__init__(*a, **kw)
        pages = self.parse(self.raw)
        self.one, self.two, self.pages = self._compile(*pages)

    def respond(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response()

       
        # Populate context.
        # =================
        
        context = request.context
        context.update(self.one)
        context['request'] = request
        context['response'] = response
        context['resource'] = self
   

        # Exec the script.
        # ================
    
        try:
            exec self.two in context 
        except Response, response:
            response = self.process_raised_response(response)
            raise response


        # Hook.
        # =====

        return self.get_response(context)


    def parse(self, raw):
        """Given a bytestring, return a list of N pages, the first two of which are python code.
        """

        # Support caret-L in addition to .
        uncareted = raw.replace("^L", PAGE_BREAK)
        pages = uncareted.split(PAGE_BREAK)
        npages = len(pages)

        # Check for too few pages.
        assert npages >= self.min_pages # sanity check; bug if False

        # Check for too many pages.
        if self.max_pages is not None and npages > self.max_pages:     # user error if True
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have exactly %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[self.max_pages]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

        return pages


    def _compile(self, one, two, *in_pages):
        """Given four items, return a 4-tuple of compiled objects.

        All dynamic resources compile the first two pages the same way. It's
        the third page that differs, so we require subclasses to provide a hook
        for that.

        """

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        one = one.replace('\r\n', '\n')
        two = two.replace('\r\n', '\n')

	pages = list(in_pages)
        for i, page in enumerate(pages):
            if page:
                pages[i] = page.replace('\r\n', '\n')


        # Compute paddings and pad the second and third pages.
        # ====================================================
        # This is so we get accurate tracebacks. We will pass padding_* to the
        # compile_* hooks in case subclasses want to use them.
        
        linesin = lambda s: '\n' * s.count('\n')
        two = linesin(one) + two 
        padding = [ linesin(two) ]
        for page in pages[:-1]:
            padding += [ padding[-1] + linesin(page) ]


        # Exec the first page and compile the second.
        # ===========================================
        # Below in render we take care not to mutate context.

        context = dict()
        context['__file__'] = self.fs
        context['website'] = self.website
        
        one = compile(one, self.fs, 'exec')
        two = compile(two, self.fs, 'exec')

        exec one in context
        one = context


        # Third and Fourth
        # ================

        for i, page in enumerate(pages):
            pages[i] = self.compile_page(page, padding[i])

        return one, two, pages


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
