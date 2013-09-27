from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.network_engines import ThreadedBuffer
from aspen.http.request import Request
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.website import Website
from aspen.testing import fix


def make_request(filename='echo.sock.spt'):
    request = Request(uri='/echo.sock')
    request.website = Website([])
    request.fs = fix(filename)
    return request

def make_socket(filename='echo.sock.spt', channel=None):
    request = make_request(filename='echo.sock.spt')
    if channel is None:
        channel = Channel(request.line.uri.path.raw, ThreadedBuffer)
    socket = Socket(request, channel)
    return socket

class SocketInThread(object):

    def __enter__(self, filename='echo.sock.spt'):
        self.socket = make_socket(filename)
        self.socket.loop.start()
        return self.socket

    def __exit__(self, *a):
        self.socket.loop.stop()
