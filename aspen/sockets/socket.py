import time
import uuid

from aspen import json, resources, Response
from aspen.sockets import HEARTBEAT, TIMEOUT, TRANSPORTS
from aspen.sockets.buffer import Buffer
from aspen.sockets.event import Event
from aspen.sockets.message import Message
from aspen.sockets.packet import Packet


class Socket(object):
    """Model a persistent Socket.IO socket (regardless of transport).

    Socket objects sit between Aspen's HTTP machinery and your Resource. They
    function as middleware, and the recv/send and _recv/_send semantics reflect
    this. They are persistent.
    
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
        request.website.copy_configuration_to(self)

        self.incoming = request.engine.Buffer()
        self.outgoing = request.engine.Buffer()
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

        It is expected that socket resources will block via self.recv() or some
        other mechanism.

        """
        exec self.resource.three in self.namespace

    def loop(self):
        """Exec the third page of the resource forever.
        """
        while 1:
            self.tick()


    # Client Side
    # ===========
    # Call these inside of your Resource.

    def sleep(self, seconds):
        """Sleep.
        """
        self.engine.sleep(seconds)

    def recv(self):
        """Block until the next message is available, then return it.
        """
        return self.incoming.next()

    def recv_utf8(self):
        """Block until the next message is available, then return it.
        """
        bytes = self.incoming.next()
        return bytes.decode('utf8')

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

    def send_utf8(self):
        """Buffer a UTF-8 message to be sent to the client.
        """
        self.__send(3, data.encode('utf8'))

    def send_json(self, data):
        """Buffer a JSON message to be sent to the client.
        """
        if not isinstance(data, basestring):
            data = json.dumps(data)
        self.__send(4, data)

    def send_event(self, data):
        """Buffer an event message to be sent to the client.
        """
        if not isinstance(data, basestring):
            data = json.dumps(data)
        self.__send(5, data)

    def __send(self, type_, data):
        message = Message()
        message.type = type_ 
        message.endpoint = self.endpoint
        message.data = data
        self.outgoing.put(message)


    # Server Side 
    # ===========
    # These are called by Aspen's HTTP machinery.

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
                self.incoming.put(message.data)
            elif message.type in (6, 7, 8): # blah, blah, blah
                pass
