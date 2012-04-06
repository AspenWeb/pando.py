from collections import deque

from aspen.sockets.buffer import ThreadedBuffer
from aspen.sockets.channel import Channel
from aspen.sockets.message import Message 
from aspen.testing.sockets import make_socket
from aspen.testing import assert_raises
from aspen.testing.fsfix import mk, attach_teardown


def test_channel_is_instantiable():
    expected = Channel
    actual = Channel('/foo.sock', ThreadedBuffer).__class__
    assert actual is expected, actual

def test_channel_can_have_sockets_added_to_it():
    mk(('echo.sock', 'channel.send(channel.recv())'))
    socket = make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)

    expected = [socket]
    actual = list(channel)
    assert actual == expected, actual

def test_channel_raises_AssertionError_on_double_add():
    mk(('echo.sock', ''))
    socket = make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)
    assert_raises(AssertionError, channel.add, socket)

def test_channel_passes_send_on_to_one_socket():
    mk(('echo.sock', ''))
    socket = make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)
    channel.send('foo')

    expected = deque([Message.from_bytes('3::/echo.sock:foo')])
    actual = socket.outgoing.queue
    assert actual == expected, actual

def test_channel_passes_send_on_to_four_sockets():
    mk(('echo.sock', 'channel.send(channel.recv())'))
    channel = Channel('foo', ThreadedBuffer)
    sockets = [make_socket(channel=channel) for i in range(4)]
    channel.send('foo')

    for socket in sockets:
        expected = deque([Message.from_bytes('3::/echo.sock:foo')])
        actual = socket.outgoing.queue
        assert actual == expected, actual

attach_teardown(globals())
