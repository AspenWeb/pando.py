import time
import uuid

from aspen import resources, Response
from aspen.sockets import HEARTBEAT, TIMEOUT, TRANSPORTS
from aspen.sockets.buffer import Buffer
from aspen.sockets.event import Event
from aspen.sockets.message import Message
from aspen.sockets.packet import Packet


class Socket(object):
    """Model a Socket.IO socket session, regardless of transport.

    Session objects sit between Aspen's HTTP machinery and your Resource. They
    function as middleware, and the recv/send and _recv/_send semantics reflect
    this.
    
    """

    transports = ",".join(TRANSPORTS)
    heartbeat = str(HEARTBEAT)
    timeout = str(TIMEOUT)


    def __init__(self, request):
        """Takes the handshake request.
        """
        self.sid = uuid.uuid4().hex
        self.endpoint = request.path.raw
        self.resource = resources.get(request)

        self.incoming = Buffer()
        self.outgoing = Buffer()
        self.namespace = self.resource.exec_second(self, request)

    def shake_hands(self):
        """Return a handshake response.
        """
        handshake = ":".join([ self.sid
                             , self.heartbeat
                             , self.timeout 
                             , self.transports
                              ])
        return Response(200, handshake)

    def tick(self):
        """Exec the third page of the resource.
        """
        exec self.resource.three in self.namespace

    def loop(self):
        """Exec the third page of the resource forever.
        """
        while 1:
            self.tick()
            time.sleep(0.010)


    # Client Side
    # ===========
    # Call these inside of your Resource.

    def recv(self):
        """Block until the next message is available, then return it.
        """
        return self.incoming.next()

    def recv_json(self):
        """Block for the next message, parse it as JSON, and return it.
        """
        bytes = self.incoming.next()
        return json.loads(bytes)

    def recv_event(self):
        """Block for the next message, parse it as an event, and return it.
        """
        bytes = self.incoming.next()
        return Event(bytes)


    def send(self, data):
        """Buffer a plain message to be sent to the client.
        """
        self.__send(3, data)

    def send_json(self, data):
        """Buffer a JSON message to be sent to the client.
        """
        self.__send(4, data)

    def send_event(self, data):
        """Buffer an event message to be sent to the client.
        """
        self.__send(5, data)

    def __send(self, type_, data):
        message = Message()
        message.type = type_ 
        message.endpoint = self.endpoint
        message.data = data
        self.outgoing.push(message)


    # Server Side 
    # ===========
    # These are called from Aspen's HTTP machinery.

    def _recv(self):
        """Return an iterator of bytes or None. Don't block.
        """
        return self.outgoing.flush()

    def _send(self, bytes):
        """Given a packet bytestring, process messages.
        """
        packet = Packet(bytes)
        for message in packet:
            if message.endpoint != self.endpoint:
                msg = "The %s endpoint got a message intended for %s."
                msg %= self.endpoint, message.endpoint
                raise RuntimeError(msg)
            if message.type == 0:           # disconnect
                pass
            elif message.type == 1:         # connect 
                pass
            elif message.type == 2:         # heartbeat
                pass
            elif message.type in (3, 4, 5): # data message
                self.incoming.push(message.data)
            elif message.type in (6, 7, 8): # blah, blah, blah
                pass
