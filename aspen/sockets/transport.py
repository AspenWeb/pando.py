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
    timeout = TIMEOUT * 0.90 # Allow for some wiggle-room to prevent XHRs
                             # from cancelling too often.

    def respond(self, request):
        """Given a Request, return a Response.
        """
        request.allow('GET', 'POST')

        if self.state == 0:             # The client wants confirmation.
            response = Response(200, "1:::")
            self.state = 1

        elif request.method == 'POST':  # The client is sending us data.
            self.socket._send(request.body.raw)
            response = Response(200)
            
        elif request.method == 'GET':   # The client is asking for data.
            bytes_iter = iter([""])
            timeout = time.time() + self.timeout
            while time.time() < timeout:
                _bytes_iter = self.socket._recv()
                if _bytes_iter is not None:
                    bytes_iter = _bytes_iter
                    break
                request.engine.sleep(0.010)
            response = Response(200, bytes_iter)

        return response

    def disconnect(self):
        pass
