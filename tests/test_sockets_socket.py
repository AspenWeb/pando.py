from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time

from aspen.sockets import FFFD
from aspen.sockets.socket import Socket


def test_socket_is_instantiable(harness):
    harness.fs.www.mk(('echo.sock.spt', ''))

    expected = Socket
    actual = harness.make_socket().__class__
    assert actual is expected

def test_two_sockets_are_instantiable(harness):
    harness.fs.www.mk(('echo.sock.spt', ''))

    socket1 = harness.make_socket()
    socket2 = harness.make_socket()

    expected = (Socket, Socket)
    actual = (socket1.__class__, socket2.__class__)
    assert actual == expected

def test_socket_can_shake_hands(harness):
    harness.fs.www.mk(('echo.sock.spt', ''))
    socket = harness.make_socket()
    response = socket.shake_hands()
    expected = '15:10:xhr-polling'
    actual = response.body.split(':', 1)[1]
    assert actual == expected

def test_socket_can_barely_function(harness):
    harness.fs.www.mk(('echo.sock.spt', 'socket.send("Greetings, program!")'))

    socket = harness.make_socket()
    socket.tick()

    expected = FFFD+b'33'+FFFD+b'3::/echo.sock:Greetings, program!'
    actual = socket._recv()
    if actual is not None:
        actual = actual.next()
    assert actual == expected

def test_socket_can_echo(harness):
    harness.fs.www.mk(('echo.sock.spt', 'socket.send(socket.recv())'))

    with harness.SocketInThread() as socket:
        socket._send(b'3::/echo.sock:Greetings, program!')
        time.sleep(0.05) # give the resource time to tick

        expected = FFFD+b'33'+FFFD+b'3::/echo.sock:Greetings, program!'
        actual = socket._recv()
        if actual is not None:
            actual = actual.next()
        assert actual == expected
