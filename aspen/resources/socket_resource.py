"""Aspen supports Socket.IO sockets. http://socket.io/
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from aspen.resources.dynamic_resource import DynamicResource


class SocketResource(DynamicResource):

    min_pages = 1
    max_pages = 4

    def respond(self):
        """Override and kill it. For sockets the Socket object responds.
        """
        raise NotImplemented

    def parse_into_pages(self, raw):
        """Extend to add empty pages to the front if there are less than three.
        """
        pages = DynamicResource.parse_into_pages(self, raw)
        self._prepend_empty_pages(pages, 3)
        return pages

    def compile_page(self, page):
        """Given two bytestrings, return a code object.

        This method depends on self.fs.

        """
        # See DynamicResource.compile_pages for an explanation of this
        # algorithm.
        return compile(page.padded_content, self.fs, 'exec')

    def exec_second(self, socket, request):
        """Given a Request, return a context dictionary.
        """
        context = request.context
        context.update(self.pages[0])
        context['socket'] = socket
        context['channel'] = socket.channel
        exec self.pages[1] in context
        return context
