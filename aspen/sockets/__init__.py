"""Implement the server side of Socket.IO.

    https://github.com/learnboost/socket.io-spec

Ah, abstraction! This is a whole convoluted mess to provide some pretty nice
API inside socket resources. Here are the objects involved on the server side:

    Message     a Socket.IO message, a colon-delimited set of strings
    Packet      a Socket.IO packet, a message or series of framed messages
    Buffer      a Socket.IO buffer, buffers incoming and outgoing messages 
    Socket      a Socket.IO socket, maintains state
    Transport   a Socket.IO transport mechanism, does HTTP work
    Resource    an HTTP resource, a file on your filesystem, business logic
    Response    an HTTP Response message
    Request     an HTTP Request message

"""
from aspen import Response

FFFD = u'\ufffd'.encode('utf-8')
HEARTBEAT = 15
TIMEOUT = 10
TRANSPORTS = ['xhr-polling']

from aspen.sockets.socket import Socket
from aspen.sockets.transport import XHRPollingTransport


__cache__ = {}


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
        socket = Socket(request)
        __cache__[socket.sid] = socket
        request.engine.spawn_socket_loop(socket)
        return socket.shake_hands()


    # More than a handshake.
    # ======================

    transport = parts[1]
    sid = parts[2]

    if transport not in TRANSPORTS:
        msg = "Expected transport in {%s}, got %s."
        msg %= (",".join(transports), transport)
        raise Response(400, msg)

    if sid not in __cache__:
        msg = "Expected %s in cache, didn't find it"
        raise Response(400, msg % sid)

    if type(__cache__[sid]) is Socket:
        # This is the first request after a handshake. It's not until this
        # point that we know what transport the client wants to use.
        Transport = XHRPollingTransport
        __cache__[sid] = Transport(__cache__[sid]) 

    transport = __cache__[sid]
    return transport
