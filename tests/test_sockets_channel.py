from collections import deque

from pytest import raises

from aspen.sockets.buffer import ThreadedBuffer
from aspen.sockets.channel import Channel
from aspen.sockets.message import Message


def test_channel_is_instantiable():
    expected = Channel
    actual = Channel('/foo.sock', ThreadedBuffer).__class__
    assert actual is expected

def test_channel_can_have_sockets_added_to_it(harness):
    harness.fs.www.mk(('echo.sock.spt', 'channel.send(channel.recv())'))
    socket = harness.make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)

    expected = [socket]
    actual = list(channel)
    assert actual == expected

def test_channel_raises_AssertionError_on_double_add(harness):
    harness.fs.www.mk(('echo.sock.spt', ''))
    socket = harness.make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)
    raises(AssertionError, channel.add, socket)

def test_channel_passes_send_on_to_one_socket(harness):
    harness.fs.www.mk(('echo.sock.spt', ''))
    socket = harness.make_socket()
    channel = Channel('foo', ThreadedBuffer)
    channel.add(socket)
    channel.send('foo')

    expected = deque([Message.from_bytes('3::/echo.sock:foo')])
    actual = socket.outgoing.queue
    assert actual == expected

def test_channel_passes_send_on_to_four_sockets(harness):
    harness.fs.www.mk(('echo.sock.spt', 'channel.send(channel.recv())'))
    channel = Channel('foo', ThreadedBuffer)
    sockets = [harness.make_socket(channel=channel) for i in range(4)]
    channel.send('foo')

    for socket in sockets:
        expected = deque([Message.from_bytes('3::/echo.sock:foo')])
        actual = socket.outgoing.queue
        assert actual == expected
