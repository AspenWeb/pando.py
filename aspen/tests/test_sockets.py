from aspen import sockets
from aspen.http.request import Request


def test_sockets_get_nonsock_returns_None():
    request = Request()
    request.socket = None
    expected = None
    actual = sockets.get(request)
    assert actual is expected, actual

