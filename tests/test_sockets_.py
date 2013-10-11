from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import sockets
from aspen.http.request import Request
from aspen.testing.sockets import make_request


def test_sockets_get_nonsock_returns_None():
    request = Request()
    request.socket = None
    expected = None
    actual = sockets.get(request)
    assert actual is expected

def test_sockets_get_adds_channel(mk):
    mk(('echo.sock.spt', '[---]\n'))
    request = make_request()
    request.socket = '1/'

    try:
        sockets.get(request) # handshake

        expected = '/echo.sock'
        actual = sockets.__channels__['/echo.sock'].name
        assert actual == expected
    finally:
        sockets.__channels__['/echo.sock'].disconnect_all()

def test_channel_survives_transportation(mk):
    mk(('echo.sock.spt', '[---]\n'))
    request = make_request()
    request.socket = '1/'
    response = sockets.get(request) # handshake
    sid = response.body.split(':')[0]
    request.socket = '1/xhr-polling/' + sid
    transport = sockets.get(request)   # transport

    try:
        expected = '/echo.sock'
        actual = sockets.__channels__['/echo.sock'].name
        assert actual == expected

        expected = transport.socket.channel
        actual = sockets.__channels__['/echo.sock']
        assert actual is expected
    finally:
        transport.socket.disconnect()


