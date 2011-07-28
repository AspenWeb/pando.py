import os
import time

from aspen.engines import ThreadedBuffer, ThreadedLoop
from aspen.http.request import Request
from aspen.sockets import FFFD
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.sockets.message import Message
from aspen.tests.fsfix import mk, attach_teardown
from aspen.website import Website


def make_request(filename='echo.sock'):
    request = Request(url='/echo.sock')
    request.website = Website([])
    request.website.copy_configuration_to(request)
    request.fs = os.sep.join([os.path.dirname(__file__), 'fsfix', filename])
    return request

def make_socket(filename='echo.sock', channel=None):
    request = make_request(filename='echo.sock')
    if channel is None:
        channel = Channel(request.path.raw, ThreadedBuffer)
    socket = Socket(request, channel)
    return socket

class SocketInThread(object):

    def __enter__(self, filename='echo.sock'):
        self.socket = make_socket(filename) 
        self.socket.loop.start()
        return self.socket

    def __exit__(self, *a):
        self.socket.loop.stop()


def test_socket_is_instantiable():
    mk(('echo.sock', ''))

    expected = Socket
    actual = make_socket().__class__
    assert actual is expected, actual

def test_two_sockets_are_instantiable():
    mk(('echo.sock', ''))

    socket1 = make_socket()
    socket2 = make_socket()

    expected = (Socket, Socket)
    actual = (socket1.__class__, socket2.__class__)
    assert actual == expected, actual

def test_socket_can_shake_hands():
    mk(('echo.sock', ''))
    socket = make_socket()
    response = socket.shake_hands()
    expected = '15:10:xhr-polling'
    actual = response.body.split(':', 1)[1]
    assert actual == expected, actual

def test_socket_can_barely_function():
    mk(('echo.sock', 'socket.send("Greetings, program!")'))

    socket = make_socket()
    socket.tick()

    expected = FFFD+'33'+FFFD+'3::/echo.sock:Greetings, program!'
    actual = socket._recv().next()
    assert actual == expected, actual

def test_socket_can_echo():
    mk(('echo.sock', 'socket.send(socket.recv())'))

    with SocketInThread() as socket:
        socket._send('3::/echo.sock:Greetings, program!')
        time.sleep(0.05) # give the resource time to tick

        expected = FFFD+'33'+FFFD+'3::/echo.sock:Greetings, program!'
        actual = socket._recv().next()
        assert actual == expected, actual

attach_teardown(globals())
