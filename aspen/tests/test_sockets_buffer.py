from aspen.sockets import FFFD
from aspen.sockets.buffer import Buffer
from aspen.sockets.message import Message


def test_buffer_is_instantiable():
    expected = Buffer
    actual = Buffer().__class__
    assert actual is expected, actual

def test_can_put_onto_buffer():
    buffer = Buffer()
    expected = [FFFD+'4'+FFFD+'1:::']
    buffer.put(Message.from_bytes('1:::'))
    actual = list(buffer.flush())
    assert actual == expected, actual

def test_buffer_flush_performance():

    return # This test makes my lap hot.

    M = lambda: Message.from_bytes("3::/echo.sock:Greetings, program!")
    N = 10000
    buffer = Buffer([M() for i in range(N)])
    out = list(buffer.flush())
    nbuffer = len(buffer)
    nout = len(out)
    assert nbuffer + nout == N, (nbuffer, nout)
    assert nout > 500
