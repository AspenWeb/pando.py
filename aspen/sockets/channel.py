class Channel(list):
    """Model a pub/sub channel as a list of socket objects.
    """

    def __init__(self, name, Buffer):
        """Takes a bytestring and Buffer class.
        """
        self.name = name
        self.incoming = Buffer('incoming')

    def add(self, socket):
        """Override to check for sanity.
        """
        assert socket not in self # sanity check
        self.append(socket)

    def disconnect_all(self):
        for i in range(len(self)):
            self[i].disconnect()

    def recv(self):
        return self.incoming.next()

    def send(self, data):
        for socket in self:
            socket.send(data)
