import time
import uuid

from aspen import json, resources, Response
from aspen.sockets import HEARTBEAT, TIMEOUT, TRANSPORTS
from aspen.sockets.event import Event
from aspen.sockets.message import Message
from aspen.sockets.packet import Packet


class Socket(object):
    """Model a persistent Socket.IO socket (regardless of transport).

    Socket objects sit between Aspen's HTTP machinery and your Resource. They
    function as middleware, and the recv/send and _recv/_send semantics reflect
    this. They (the sockets) are persistent.
    
    """

    transports = ",".join(TRANSPORTS)
    heartbeat = str(HEARTBEAT)
    timeout = str(TIMEOUT)


    def __init__(self, request, channel):
        """Takes the handshake request and the socket's channel.
        """
        self.sid = uuid.uuid4().hex
        self.endpoint = request.path.raw
        self.resource = resources.get(request)
        request.website.copy_configuration_to(self)
        request.website.copy_configuration_to(channel)

        self.loop = request.engine.Loop(self)
        self.incoming = request.engine.Buffer('incoming', self)
        self.outgoing = request.engine.Buffer('outgoing', self)
        self.channel = channel
        self.channel.add(self)
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
        other mechanism, like reading a remote TCP socket.

        """
        exec self.resource.three in self.namespace

    def disconnect(self):
        self.loop.stop()
        exec self.resource.four in self.namespace
        self.channel.remove(self)


    # Client Side
    # ===========
    # Call these inside of your Resource.

    def sleep(self, seconds):
        """Block until seconds have elapsed.
        """
        self.engine.sleep(seconds)

    def recv(self):
        """Block until the next message is available, then return it.
        """
        return self.incoming.next()


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

   
    # Event API
    # =========
    # Working with events is so common that we offer these conveniences.

    def listen(self, *filter):
        """Given a series of events to listen for, return a tuple.
    
        The return value is a tuple of the event name and data. If no events
        are specified, the first event is returned.

        """
        while 1:
            msg = self.incoming.next()
            if not filter or msg['name'] in filter:
                break
        return (msg['name'], msg['args'])

    def notify(self, name, *args):
        """This is a convenience function for event notification.

        The first argument is the name of the event, and subsequent arguments
        show up as the arguments to the callback function in your event
        listener on the client side.

        """
        self.send_event({"name": name, "args": args})


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
            # https://github.com/learnboost/socket.io-spec
            if message.endpoint != self.endpoint:
                msg = "The %s endpoint got a message intended for %s."
                msg %= self.endpoint, message.endpoint
                raise RuntimeError(msg)
            if message.type == 0:           # disconnect
                self.disconnect()
            elif message.type == 1:         # connect 
                pass
            elif message.type == 2:         # heartbeat
                pass
            elif message.type in (3, 4, 5): # data message
                self.incoming.put(message.data)
                self.channel.incoming.put(message.data)
            elif message.type in (6, 7, 8): # blah, blah, blah
                pass
