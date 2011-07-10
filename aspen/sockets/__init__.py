"""Implement the server side of Socket.IO.

https://github.com/learnboost/socket.io-spec

Ah, abstraction! This is a whole convoluted mess to provide some pretty nice
API inside socket resources. Here are the objects involved on the server side:

    Request     an HTTP Request message
    Response    an HTTP Response message
    Resource    an HTTP resource
    Socket      a Socket.IO socket, unbound to a transport mechanism
    Transported a Socket.IO socket, bound to a transport mechanism

"""
from aspen import resources, Response
from aspen.sockets.socket_ import Socket
from aspen.sockets.transported import XHRPollingSocket


__cache__ = {}


def get(request):
    """Takes a Request object and returns a Response or Transport object.

    When we get the request it has socket set to a string, the path part after
    *.sock, which is something like 1/websocket/43ef6fe7?foo=bar.

        1           protocol (we only support 1)
        websocket   transport
        43ef6fe7    socket id (sid)
        ?foo=bar    querystring

    The socket.io handshake is a GET request to 1/. We return Response for the
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
        print "shaking hands"
        socket = Socket(request)
        __cache__[socket.sid] = socket
        return socket.shake_hands()


    # More than a handshake.
    # ======================

    print "transporting"
    transport = parts[1]
    sid = parts[2]

    if transport not in TRANSPORTS:
        msg = "Expected transport in {%s}, got %s."
        msg %= (",".join(transports), transport)
        raise Response(400, msg)

    if sid not in __cache__:
        msg = "Expected %s in cache, didn't find it"
        raise Response(400, msg % sid)

    if isinstance(__cache__[sid], Socket):
        # This is the first request after a handshake. It's not until this
        # point that we know what transport the client wants to use.
        Transported = XHRPollingSocket
        __cache__[sid] = Transported(__cache__[sid]) 

    transported = __cache__[sid]
    return transported
