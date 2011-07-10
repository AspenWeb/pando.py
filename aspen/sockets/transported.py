import time

from aspen import Response


class Transported(object):
    
    def __init__(self, socket):
        """Takes a Socket base class instance.
        """
        self.socket = socket


class XHRPollingSocket(Transported):

    state = 0

    def respond(self, request):
        """
        """
        if self.state == 0:
            response = Response(200, "1::")
            self.state = 1
        elif request.method == 'POST':
            self.socket._recv(request.body.raw)
            response = Response(200) # XXX?
        elif request.method == 'GET':
            bytes = ""
            timeout = time.time() + TIMEOUT - 1
            while not bytes and time.time() < timeout: # XXX timeout 
                time.sleep(0.5)
                bytes = self.socket._send()
            response = Response(200, bytes)
        else:
            raise Response(405, headers={'Allow': 'GET, POST'})
        return response


