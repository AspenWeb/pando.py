from aspen.sockets.packet import Packet


def test_packet_instantiable_with_unframed_bytes():
    expected = '1:::'
    actual = str(Packet('1:::'))
    assert actual == expected, actual

