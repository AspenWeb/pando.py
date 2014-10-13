"""
aspen.resources.dynamic_resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import Response
from aspen.resources.pagination import split_and_escape, Page
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
    """This is the base for negotiating and rendered resources.
    """

    min_pages = None  # set on subclass
    max_pages = None

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)
        pages = self.parse_into_pages(self.raw)
        self.pages = self.compile_pages(pages)


    def respond(self, request, dispatch_result, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response(charset=self.website.charset_dynamic)


        # Populate context.
        # =================

        context = self.populate_context(request, dispatch_result, response)


        # Exec page two.
        # ==============

        try:
            exec self.pages[1] in context
        except Response, response:
            self.process_raised_response(response)
            raise

        # if __all__ is defined, only pass those variables to templates
        # if __all__ is not defined, pass full context to templates

        if '__all__' in context:
            newcontext = dict([ (k, context[k]) for k in context['__all__'] ])
            context = newcontext

        # Hook.
        # =====

        try:
            response = self.get_response(context)
        except Response, response:
            self.process_raised_response(response)
            raise
        else:
            return response


    def populate_context(self, request, dispatch_result, response):
        """Factored out to support testing.
        """
        dynamics = { 'body' : lambda: request.body }
        class Context(dict):
            def __getitem__(self, key):
                if key in dynamics:
                    return dynamics[key]()
                return dict.__getitem__(self, key)
        context = Context()
        context.update(request.context)
        context.update({
            'website': None,
            'headers': request.headers,
            'cookie': request.headers.cookie,
            'path': request.line.uri.path,
            'qs': request.line.uri.querystring,
            'channel': None
        })
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
        for method in ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT']:
            context[method] = (method == request.line.method)
        # insert the residual context from the initialization page
        context.update(self.pages[0])
        # don't let the page override these
        context.update({
            'request' : request,
            'dispatch_result': dispatch_result,
            'resource': self,
            'response': response
        })
        return context


    def parse_into_pages(self, raw):
        """Given a bytestring, return a list of pages.

        Subclasses extend this to implement additional semantics.

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

        # Subclasses are responsible for the rest.
        # ========================================

        pages[2:] = (self.compile_page(page) for page in pages[2:])

        return pages

    @staticmethod
    def _prepend_empty_pages(pages, min_length):
        """Given a list of pages, and a min length, prepend blank pages to the
        list until it is at least as long as min_length
        """
        num_extra_pages = min_length - len(pages)
        #Note that range(x) returns an empty list if x < 1
        pages[0:0] = (Page('') for _ in range(num_extra_pages))

    # Hooks
    # =====

    def compile_page(self, *a):
        """Given a page, return an object.
        """
        raise NotImplementedError

    def process_raised_response(self, response):
        """Given a response object, mutate it as needed.
        """
        pass

    def get_response(self, context):
        """Given a context dictionary, return a Response object.
        """
        raise NotImplementedError
