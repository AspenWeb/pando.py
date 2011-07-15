from aspen.sockets.buffer import Buffer
from aspen.sockets.message import Message


def test_buffer_is_instantiable():
    expected = Buffer
    actual = Buffer().__class__
    assert actual is expected, actual

def test_can_push_onto_buffer():
    buffer = Buffer()
    expected = ['1:::']
    buffer.push(Message.from_bytes('1:::'))
    actual = list(buffer.flush())
    assert actual == expected, actual
