from __future__ import with_statement # for Python 2.5
import time

from aspen.sockets import FFFD
from aspen.sockets.socket import Socket
from aspen.testing.fsfix import mk, attach_teardown
from aspen.testing.sockets import make_socket, SocketInThread


def test_socket_is_instantiable():
    mk(('echo.sock.spt', ''))

    expected = Socket
    actual = make_socket().__class__
    assert actual is expected, actual

def test_two_sockets_are_instantiable():
    mk(('echo.sock.spt', ''))

    socket1 = make_socket()
    socket2 = make_socket()

    expected = (Socket, Socket)
    actual = (socket1.__class__, socket2.__class__)
    assert actual == expected, actual

def test_socket_can_shake_hands():
    mk(('echo.sock.spt', ''))
    socket = make_socket()
    response = socket.shake_hands()
    expected = '15:10:xhr-polling'
    actual = response.body.split(':', 1)[1]
    assert actual == expected, actual

def test_socket_can_barely_function():
    mk(('echo.sock.spt', 'socket.send("Greetings, program!")'))

    socket = make_socket()
    socket.tick()

    expected = FFFD+'33'+FFFD+'3::/echo.sock:Greetings, program!'
    actual = socket._recv()
    if actual is not None:
        actual = actual.next()
    assert actual == expected, actual

def test_socket_can_echo():
    mk(('echo.sock.spt', 'socket.send(socket.recv())'))

    with SocketInThread() as socket:
        socket._send('3::/echo.sock:Greetings, program!')
        time.sleep(0.05) # give the resource time to tick

        expected = FFFD+'33'+FFFD+'3::/echo.sock:Greetings, program!'
        actual = socket._recv()
        if actual is not None:
            actual = actual.next()
        assert actual == expected, actual

attach_teardown(globals())
