import collections
import uuid


TRANSPORTS = ['xhr-polling']
HEARTBEAT = 15
TIMEOUT = 10


class Socket(object):
    """Model a Socket.IO socket, regardless of transport.
    """

    transports = ",".join(TRANSPORTS)
    heartbeat = str(HEARTBEAT)
    timeout = str(TIMEOUT)


    def __init__(self, request):
        """Takes the handshake request.
        """
        self.sid = uuid.uuid4().hex
        self.resource = resources.get(request)

        self.incoming = collections.deque()
        self.outgoing = collections.deque()
        self.namespace = self.resource.exec_second(self, request)
        request.website.engine.spawn_socket_handler(self)

    def shake_hands(self):
        """Return a handshake response.
        """
        handshake = ":".join([ self.sid
                             , self.heartbeat
                             , self.timeout 
                             , self.transports
                              ])
        return Response(200, handshake)

    def loop(self):
        """Exec the third page of the resource forever.
        """
        while 1:
            print "queues", self.incoming, self.outgoing
            exec self.resource.three in self.namespace
    

    # Call these inside of your resource.
    # ===================================

    def recv(self):
        """Yield one message at a time. Block.
        """
        while 1:
            nmessages = len(self.incoming)
            if nmessages > 0:
                for i in range(nmessages):
                    yield self.incoming.pop()
            time.sleep(0.5)

    def send(self, msg):
        """Queue a message to be sent to the client.
        """
        msg = "3:1:echo.sock:%s" % msg
        self.outgoing.appendleft(msg)


    # Private
    # =======

    def _pack(self, msg):
        if not isinstance(msg, str):
            msg = msg.encode('utf-8') # to bytestring
        msg = '%s%d%s%s' % (FFFD, len(msg), FFFD, msg)
        return msg

    def _recv(self, bytes):
        """Given bytes, append to incoming.
        """
        messages = Messages(bytes)
        for message in messages:
            if message.type in (3, 4, 5):
                self.incoming.appendleft(unencoded)

    def _send(self):
        """Pack and return any bytes queued to be sent.
        """
        packed = ""
        nmessages = len(self.outgoing)
        if nmessages > 0:
            for i in range(nmessages):
                msg = self.outgoing.pop()
                packed += self._pack(msg)
        print "sending", packed
        return packed

