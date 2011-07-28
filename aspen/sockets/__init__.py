"""Implement the server side of Socket.IO.

    https://github.com/learnboost/socket.io-spec

Ah, abstraction! This is a whole convoluted mess to provide some pretty nice
API inside socket resources. Here are the objects involved on the server side,
from the inside out:

    Message     a Socket.IO message, a colon-delimited set of bytestrings
    Packet      a Socket.IO packet, a message or series of framed messages
    Buffer      a Socket.IO buffer, buffers incoming and outgoing messages 
    Loop        an object responsible for repeatedly calling socket.tick
    Socket      a Socket.IO socket, maintains state
    Channel     an object that represents all connections to a single Resource
    Transport   a Socket.IO transport mechanism, does HTTP work
    Resource    an HTTP resource, a file on your filesystem, application logic
    Response    an HTTP Response message
    Request     an HTTP Request message

    Engine      fits somewhere, handles networking implementation; Buffer and 
                  Loop attributes point to implementations of the above


A specially-crafted HTTP request creates a new Socket. That socket object
exists until one of these conditions is met:

    - the application explicitly disconnects
    - the client explicitly disconnects
    - the client disappears (for some definition of "disappears")

A second specially-crafted HTTP request negotiates a Transport. Subsequent
specially-crafted HTTP requests are marshalled into socket reads and writes
according to the Transport negotiated.

The Loop object is responsible for running socket.tick until it is told to stop
(as a result of one of the above three conditions). socket.tick exec's the
third page of the application's socket resource in question. This code is
expected to block. For ThreadedLoop that means we can't stop the loop inside of
native code. The ThreadedBuffer object cooperates with ThreadedLoop, so if your
application only ever blocks on socket.recv then you are okay. CooperativeLoops
should be immediately terminable assuming your application and its dependencies
cooperate ;-).

"""
from aspen import Response

FFFD = u'\ufffd'.encode('utf-8')
HEARTBEAT = 15
TIMEOUT = 10
TRANSPORTS = ['xhr-polling']

from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.sockets.transport import XHRPollingTransport


__sockets__ = {}
__channels__ = {}


def get(request):
    """Takes a Request object and returns a Response or Transport object.

    When we get the request it has socket set to a string, the path part after
    *.sock, which is something like 1/websocket/43ef6fe7?foo=bar.

        1           protocol (we only support 1)
        websocket   transport
        43ef6fe7    socket id (sid)
        ?foo=bar    querystring

    The Socket.IO handshake is a GET request to 1/. We return Response for the
    handshake. After the handshake, subsequent messages are to the full URL as
    above. We return a Transported instance for actual messages.

    """

    # Exit early.
    # ===========

    if request.socket is None:
        return None


    # Parse and validate the socket URL.
    # ==================================

    parts = request.socket.split('/')
    nparts = len(parts)
    if nparts not in (2, 3):
        msg = "Expected 2 or 3 path parts for Socket.IO socket, got %d."
        raise Response(400, msg % nparts)

    protocol = parts[0]
    if protocol != '1':
        msg = "Expected Socket.IO protocol version 1, got %s."
        raise Response(400, msg % protocol)


    # Handshake
    # =========

    if len(parts) == 2:
        if request.path.raw in __channels__:
            channel = __channels__[request.path.raw]
        else:
            channel = Channel(request.path.raw, request.engine.Buffer)
            __channels__[request.path.raw] = channel

        socket = Socket(request, channel)
        assert socket.sid not in __sockets__ # sanity check
        __sockets__[socket.sid] = socket
        socket.loop.start()

        return socket.shake_hands() # a Response


    # More than a handshake.
    # ======================

    transport = parts[1]
    sid = parts[2]

    if transport not in TRANSPORTS:
        msg = "Expected transport in {%s}, got %s."
        msg %= (",".join(transports), transport)
        raise Response(400, msg)

    if sid not in __sockets__:
        msg = "Expected %s in cache, didn't find it"
        raise Response(400, msg % sid)

    if type(__sockets__[sid]) is Socket:
        # This is the first request after a handshake. It's not until this
        # point that we know what transport the client wants to use.
        Transport = XHRPollingTransport # XXX derp
        __sockets__[sid] = Transport(__sockets__[sid]) 

    transport = __sockets__[sid]
    return transport
