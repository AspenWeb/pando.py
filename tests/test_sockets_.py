from aspen import sockets
from aspen.http.request import Request
from aspen.testing import mk, attach_teardown
from aspen.testing.sockets import make_request


def test_sockets_get_nonsock_returns_None():
    request = Request()
    request.socket = None
    expected = None
    actual = sockets.get(request)
    assert actual is expected, actual

def test_sockets_get_adds_channel():
    mk(('echo.sock', ''))
    request = make_request()
    request.socket = '1/'
    try:
        response = sockets.get(request) # handshake

        expected = '/echo.sock' 
        actual = sockets.__channels__['/echo.sock'].name
        assert actual == expected, actual
    finally:
        sockets.__channels__['/echo.sock'].disconnect_all()

def test_channel_survives_transportation():
    mk(('echo.sock', ''))
    request = make_request()
    request.socket = '1/'
    try:
        response = sockets.get(request) # handshake
        sid = response.body.split(':')[0]
        request.socket = '1/xhr-polling/' + sid
        transport = sockets.get(request)   # transport

        expected = '/echo.sock' 
        actual = sockets.__channels__['/echo.sock'].name
        assert actual == expected, actual

        expected = transport.socket.channel
        actual = sockets.__channels__['/echo.sock']
        assert actual is expected, actual
    finally:
        transport.socket.disconnect()

attach_teardown(globals())
