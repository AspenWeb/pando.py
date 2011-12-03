from aspen import Response
from aspen.resources.resource import Resource


PAGE_BREAK = chr(12)

# Global page limits. There are further limits per-resource-type.
MIN_PAGES = 2
MAX_PAGES = 4

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
        assert MIN_PAGES <= self.max_pages <= MAX_PAGES # sanity check
        super(DynamicResource, self).__init__(*a, **kw)
        pages = self._parse(self.raw)
        self.one, self.two, self.three, self.four = self._compile(*pages)

    def respond(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response()

       
        # Populate namespace.
        # ===================
        
        namespace = self.one.copy()
        namespace.update(request.namespace)
        namespace['request'] = request
        namespace['response'] = response
   

        # Exec the script.
        # ================
    
        try:
            exec self.two in namespace
        except Response, response:
            response = self.process_raised_response(response)
            raise response


        # Hook.
        # =====

        return self.get_response(namespace)


    def _parse(self, raw):
        """Given a bytestring, return a list of four items.
        
        If there are too few pages, raise AssertionError. Any resource with
        only one page should land in StaticResource, not here.
        
        If there are too many pages, raise SyntaxError. 

        If there are fewer than self.max_pages, then pad the front of the list
        with up to two empty strings, and the end with up to one.

        If self.max_pages is less than four (i.e., three or two), pad the end
        of the list with None.
        
        """

        # Support caret-L in addition to .
        uncareted = raw.replace("^L", PAGE_BREAK)
        pages = uncareted.split(PAGE_BREAK)
        npages = len(pages)

        # Check for too few pages.
        assert npages >= self.min_pages # sanity check; bug if False

        # Check for too many pages.
        if npages > self.max_pages:     # user error if True
            type_name = self.__class__.__name__[:-len('resource')]
            msg = "%s resources must have exactly %s pages; %s has %s."
            msg %= ( type_name
                   , ORDINALS[self.max_pages]
                   , self.fs
                   , ORDINALS[npages]
                    )
            raise SyntaxError(msg)

        # Pad front (and back?) with empty strings.
        while len(pages) < (self.max_pages - 1):
            pages.insert(0, '')
        if len(pages) < self.max_pages:
            pages.append('')


        # Pad the back with None.
        while len(pages) < MAX_PAGES:
            pages.append(None)

        return pages
       
    def _compile(self, one, two, three, four):
        """Given fouritems, return a 4-tuple of compiled objects.

        All dynamic resources compile the first two pages the same way. It's
        the third page that differs, so we require subclasses to provide a hook
        for that.

        """

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        one = one.replace('\r\n', '\n')
        two = two.replace('\r\n', '\n')
        if three is not None:
            three = three.replace('\r\n', '\n')


        # Compute paddings and pad the second and third pages.
        # ====================================================
        # This is so we get accurate tracebacks. We will pass padding_* to the
        # compile_* hooks in case subclasses want to use them.
        
        padding = lambda s: ''.join(['\n' for n in range(s.count('\n'))])
        padding_two = padding(one)
        padding_three = padding_two + padding(two)
        two = padding_two + two 


        # Exec the first page and compile the second.
        # ===========================================
        # Below in render we take care not to mutate namespace.

        namespace = dict()
        namespace['__file__'] = self.fs
        namespace['website'] = self.website
        
        one = compile(one, self.fs, 'exec')
        two = compile(two, self.fs, 'exec')

        exec one in namespace
        one = namespace


        # Third and Fourth
        # ================

        three = self.compile_third(one, two, three, padding_two)
        four = self.compile_fourth(one, two, three, four, padding_three)


        return one, two, three, four


    # Hooks
    # =====

    def compile_third(self, *a):
        """Given a bytestring, return an object.
        """
        raise NotImplementedError

    def compile_fourth(self, *a):
        """Given a bytestring, return an object.
        """
        raise NotImplementedError

    def process_raised_response(self, response):
        """Given a response object, return a response object.
        """
        return response

    def get_response(self, namespace):
        """Given a namespace dictionary, return a Response object.
        """
        raise NotImplementedError
