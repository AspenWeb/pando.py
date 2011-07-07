"""Implement the server side of Socket.IO.

https://github.com/learnboost/socket.io-spec

"""
import uuid
from aspen import Response


TRANSPORTS = ['xhr-polling']
FFFD = u'\ufffd'.encode('utf-8')


__cache__ = {}


def get(request):
    """Takes a Request object.

    The path after *.sock is something like 1/websocket/43ef6fe7?foo=bar.

    The socket.io handshake is a GET request to 1/. After the handshake,
    subsequent messages are to 1/%transport/%sid?%query.

    """
    return None
    parts = request.path.raw.split('.sock/')
    socket = None
    if len(parts) == 1:
        return None
        request.path.raw = parts[0] + '.sock'
        socket = socket_io.get_socket(parts[1], request)


    # Parse and validate the input.
    # =============================

    parts = request.fs.split('/')
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
        sid = uuid.uuid4().hex
        heartbeat = str(15)
        timeout = str(10)
        transports = ",".join(TRANSPORTS)

        __cache__[sid] = None

        handshake = ":".join([sid, heartbeat, timeout, transports])

        response = Response(200)
        response.body = handshake
        raise response # TODO return would be faster


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

    if __cache__[sid] is None:
        # This is the first request after a handshake. It's not until this
        # point that we know what transport the client wants to use.
        SpecificSocket = XHRPollingSocket
        __cache__[sid] = SpecificSocket(sid) 

    socket = __cache__[sid]
    return socket 


class Socket(object):
    """Base class.
    """

    def __init__(self, sid):
        self.sid = sid


class XHRPollingSocket(Socket):

    def handle(self, request):
        """
        """
        if request.method == 'POST':
            message = request.socket.recv()
            request.socket.send(messages[0]) 
        else:
            while 1:
                if request.socket.messages:
                    request.socket.send("1::")
                time.sleep(0.5)

        response = Response(200)
        response.body = ""
        return response

    def recv(self):
        raw = self.request.body.raw
        frames = raw.split(FFFD)
        frames.pop() # packet starts with FFFD
        assert len(frames) % 2 == 0, "Odd number of frames!"
        messages = []
        while frames:
            nbytes = frames.pop()
            bytes = frames.pop()
            messages.append(bytes)
        return messages 

    def send(self, msg):
        response = Response(200)
        msg = msg.encode('utf-8')
        msg = '%s%d%s%s' % (FFFD, len(msg), FFFD, msg)
        response.body = msg
        raise response
