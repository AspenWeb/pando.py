from aspen.network_engines import ThreadedBuffer
from aspen.http.request import Request
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.website import Website
from aspen.testing import fix


def make_request(filename='echo.sock'):
    request = Request(uri='/echo.sock')
    request.website = Website([])
    request.fs = fix(filename)
    return request

def make_socket(filename='echo.sock', channel=None):
    request = make_request(filename='echo.sock')
    if channel is None:
        channel = Channel(request.line.uri.path.raw, ThreadedBuffer)
    socket = Socket(request, channel)
    return socket

class SocketInThread(object):

    def __enter__(self, filename='echo.sock'):
        self.socket = make_socket(filename)
        self.socket.loop.start()
        return self.socket

    def __exit__(self, *a):
        self.socket.loop.stop()
