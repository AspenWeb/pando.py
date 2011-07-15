import time

from aspen import Response
from aspen.sockets import TIMEOUT


class Transport(object):
    """A transport converts HTTP messages into Socket messages.
    """
    
    def __init__(self, socket):
        """Takes a Socket instance.
        """
        self.socket = socket


class XHRPollingTransport(Transport):

    state = 0

    def respond(self, request):
        """Given a Request, return a Response.
        """
        request.allow('GET', 'POST')
        if self.state == 0:
            # Socket.IO wants confirmation.
            response = Response(200, "1:::")
            self.state = 1
        elif request.method == 'POST':
            # The client is sending us data.
            self.socket._send(request.body.raw)
            response = Response(200) # XXX What's the proper response here?
        elif request.method == 'GET':
            # The client is asking for data.
            bytes = ""
            timeout = time.time() + TIMEOUT - 1
            while not bytes and time.time() < timeout:
                time.sleep(0.01)
                bytes = self.socket._recv()
            response = Response(200, bytes)
        return response


