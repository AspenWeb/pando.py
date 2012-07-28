"""Aspen supports Socket.IO sockets. http://socket.io/
"""
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
        while len(pages) < 3:
            pages = [''] + pages
        return pages

    def compile_page(self, page, padding):
        """Given two bytestrings, return a code object.

        This method depends on self.fs.

        """
        # See DynamicResource.compile_pages for an explanation of this
        # algorithm.
        page = page.replace('\r\n', '\n')
        page = padding + page
        page = compile(page, self.fs, 'exec')
        return page

    def exec_second(self, socket, request):
        """Given a Request, return a context dictionary.
        """
        context = request.context
        context.update(self.pages[0])
        context['socket'] = socket
        context['channel'] = socket.channel
        exec self.pages[1] in context
        return context
