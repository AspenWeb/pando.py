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

    def send(self, data):
        for socket in self:
            socket.send(data)

    def send_event(self, data):
        for socket in self:
            socket.send_event(data)

    def send_json(self, data):
        for socket in self:
            socket.send_json(data)

    def send_utf8(self, data):
        for socket in self:
            socket.send_utf8(data)

    def notify(self, name, *args):
        for socket in self:
            socket.notify(name, *args)
