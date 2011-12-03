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

    def compile_third(self, one, two, three, padding):
        """Given four bytestrings, return a code object.

        This method depends on self.fs.

        """
        # See DyanmicResource._compile for comments on this algorithm.
        three = three.replace('\r\n', '\n')
        three = padding + three
        three = compile(three, self.fs, 'exec')
        return three

    def compile_fourth(self, one, two, three, four, padding):
        """Given five bytestrings, return a code object.

        This method depends on self.fs.

        """
        # See DyanmicResource._compile for comments on this algorithm.
        four = four.replace('\r\n', '\n')
        four = padding + four
        four = compile(four, self.fs, 'exec')
        return four

    def exec_second(self, socket, request):
        """Given a Request, return a namespace dictionary.
        """
        namespace = self.one.copy()
        namespace.update(request.namespace)
        namespace['request'] = request 
        namespace['socket'] = socket
        namespace['channel'] = socket.channel
        exec self.two in namespace
        return namespace
