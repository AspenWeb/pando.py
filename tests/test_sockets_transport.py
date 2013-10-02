from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from collections import deque
from cStringIO import StringIO

from aspen import Response
from aspen.http.request import Request
from aspen.sockets import FFFD
from aspen.sockets.transport import XHRPollingTransport
from aspen.sockets.message import Message
from aspen.testing.sockets import make_socket, make_request
from aspen.testing.fsfix import teardown_function, mk


def make_transport(content='', state=0):
    mk(('echo.sock.spt', content))
    socket = make_socket()
    transport = XHRPollingTransport(socket)
    transport.timeout = 0.05 # for testing, could screw up the test
    if state == 1:
        transport.respond(Request(uri='/echo.sock'))
    return transport


def test_transport_instantiable():
    transport = make_transport()

    expected = XHRPollingTransport
    actual = transport.__class__
    assert actual is expected

def test_transport_can_minimally_respond():
    transport = make_transport()
    request = Request()

    expected = Response
    actual = transport.respond(request).__class__
    assert actual is expected

def test_transport_starts_in_state_0():
    transport = make_transport()
    request = Request()

    expected = 0
    actual = transport.state
    assert actual == expected

def test_transport_goes_to_state_1_after_first_request():
    transport = make_transport()
    request = Request()
    transport.respond(request)

    expected = 1
    actual = transport.state
    assert actual == expected

def test_transport_stays_in_state_1_after_second_request():
    transport = make_transport()
    request = make_request()
    transport.respond(request)
    transport.respond(request)

    expected = 1
    actual = transport.state
    assert actual == expected

def test_transport_POST_gives_data_to_socket():
    transport = make_transport(state=1)

    request = Request( 'POST'
                     , '/echo.sock'
                     , body=StringIO(b'3::/echo.sock:Greetings, program!')
                      )
    transport.respond(request)

    expected = deque(['Greetings, program!'])
    actual = transport.socket.incoming.queue
    assert actual == expected

def test_transport_GET_gets_data_from_socket():
    transport = make_transport(state=1)
    message = Message.from_bytes(b"3:::Greetings, program!")
    transport.socket.outgoing.put(message)

    request = Request('GET')
    response = transport.respond(request)

    expected = FFFD+b'23'+FFFD+b'3:::Greetings, program!'
    actual = response.body.next()
    assert actual == expected

def test_transport_GET_blocks_for_empty_socket():
    transport = make_transport(state=1)

    request = make_request()
    start = time.time()
    response = transport.respond(request)
    end = time.time()

    expected = transport.timeout
    actual = round(end - start, 4)
    assert actual > expected

def test_transport_handles_roundtrip():
    transport = make_transport(state=1, content="socket.send(socket.recv())")

    request = Request('POST', '/echo.sock', body=StringIO(b"3::/echo.sock:ping"))
    transport.respond(request)
    transport.socket.tick() # do it manually

    request = Request('GET', '/echo.sock')
    response = transport.respond(request)

    expected = FFFD+b"18"+FFFD+b"3::/echo.sock:ping"
    actual = response.body.next()
    assert actual == expected



