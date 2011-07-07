from aspen import Response
from aspen.resources.resource import Resource


PAGE_BREAK = chr(12)


class DynamicResource(Resource):
    """This is a base class for json, socket, and template resources.
    """

    def __init__(self, *a, **kw):
        super(DynamicResource, self).__init__(*a, **kw)
      
        # Support caret-L in addition to .
        careted = self.raw.replace("^L", PAGE_BREAK)
        pages = careted.split(PAGE_BREAK)
        npages = len(pages)
        assert npages > 1 # Check sanity. If we only have one page we should be
                          # served by StaticResource. Right?
        self.compile(npages, pages)

    def render(self, request, response=None):
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
    
        exec self.two in namespace
        response = namespace['response']


        # Hook.
        # =====
    
        self.mutate(namespace)

        
        # Set the mimetype.
        # =================
        # We guessed based on the filesystem path, not the URL path. 
        
        if response.headers.one('Content-Type') is None:
            response.headers.set('Content-Type', self.mimetype)


        # Send it on back up the line.
        # ============================

        return response


    # Hooks
    # =====

    def compile(self, npages, pages):
        """Given an int and a sequence of bytestrings, set attributes on self.
        """
        raise NotImplementedError

    def mutate(self, namespace):
        """Given a namespace dictionary, mutate it.
        """
        raise NotImplementedError


    # Helper
    # ======

    def compile_python(self, one, two):
        """Given two bytestrings of Python, return a dict and a code object.
        """

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        one = one.replace('\r\n', '\n')
        two = two.replace('\r\n', '\n')


        # Pad the beginning of the second page.
        # =====================================
        # This is so we get accurate tracebacks. We used to do this for the
        # template page too, but Tornado templates have some weird error 
        # handling that we haven't exposed yet.

        padding = ''.join(['\n' for n in range(one.count('\n'))])
        two = padding + two 


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

        return one, two
