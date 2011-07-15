import os

from aspen.tests.fsfix import mk, attach_teardown
from aspen.http.request import Request
from aspen.sockets.socket import Socket
from aspen.sockets.message import Message
from aspen.website import Website


def make_socket(filename='echo.sock'):
    request = Request()
    request.website = Website([])
    request.fs = os.sep.join([os.path.dirname(__file__), 'fsfix', filename])
    return Socket(request)


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

    expected = '3:::Greetings, program!'
    actual = socket._recv().next()
    assert actual == expected, actual

def test_socket_can_echo():
    mk(('echo.sock', 'socket.send(socket.recv())'))
    
    socket = make_socket() 
    socket._send('3:::Greetings, program!')
    socket.tick()

    expected = '3:::Greetings, program!'
    actual = socket._recv().next()
    assert actual == expected, actual


attach_teardown(globals())
