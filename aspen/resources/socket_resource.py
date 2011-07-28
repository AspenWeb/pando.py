from aspen.resources.dynamic_resource import DynamicResource


class SocketResource(DynamicResource):

    max_pages = 1
    max_pages = 3

    def respond(self):
        """Override and kill it. For sockets the Socket object responds.
        """
        raise NotImplemented

    def compile_third(self, one, two, three, padding):
        """Given three bytestrings, return a code object.

        This method depends on self.fs.

        """
        # See DyanmicResource._compile for comments on this algorithm.
        three = three.replace('\r\n', '\n')
        three = padding + three
        three = compile(three, self.fs, 'exec')
        return three

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

