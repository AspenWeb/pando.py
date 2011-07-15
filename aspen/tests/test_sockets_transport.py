import time
from collections import deque

from aspen import Response
from aspen.http.request import Request
from aspen.sockets import TIMEOUT
from aspen.sockets.transport import XHRPollingTransport
from aspen.sockets.message import Message
from aspen.tests.test_sockets_socket import make_socket
from aspen.tests.fsfix import attach_teardown, mk


def make_transport(content='', state=0):
    mk(('echo.sock', content))
    socket = make_socket()
    transport = XHRPollingTransport(socket)
    transport.timeout = 0.05
    if state == 1:
        transport.respond(Request())
    return transport


def test_transport_instantiable():
    transport = make_transport()

    expected = XHRPollingTransport
    actual = transport.__class__
    assert actual is expected, actual

def test_transport_can_minimally_respond():
    transport = make_transport()
    request = Request()

    expected = Response
    actual = transport.respond(request).__class__
    assert actual is expected, actual
    
def test_transport_starts_in_state_0():
    transport = make_transport()
    request = Request()
    
    expected = 0
    actual = transport.state
    assert actual == expected, actual
    
def test_transport_goes_to_state_1_after_first_request():
    transport = make_transport()
    request = Request()
    transport.respond(request)

    expected = 1 
    actual = transport.state
    assert actual == expected, actual

def test_transport_stays_in_state_1_after_second_request():
    transport = make_transport()
    request = Request()
    transport.respond(request)
    transport.respond(request)
    
    expected = 1 
    actual = transport.state
    assert actual == expected, actual
    
def test_transport_POST_gives_data_to_socket():
    transport = make_transport(state=1)

    request = Request('POST', body='3:::Greetings, program!')
    transport.respond(request)
   
    expected = deque(['Greetings, program!'])
    actual = transport.socket.incoming
    assert actual == expected, actual
    
def test_transport_GET_gets_data_from_socket():
    transport = make_transport(state=1)
    message = Message.from_bytes("3:::Greetings, program!")
    transport.socket.outgoing.push(message)
    
    request = Request('GET')
    response = transport.respond(request)
   
    expected = '3:::Greetings, program!'
    actual = response.body.next()
    assert actual == expected, actual
    
def test_transport_GET_blocks_for_empty_socket():
    transport = make_transport(state=1)
    
    request = Request('GET')
    start = time.time()
    response = transport.respond(request)
    end = time.time()
 
    expected = transport.timeout
    actual = end - start
    assert actual > expected, actual

def test_transport_handles_roundtrip():
    transport = make_transport(state=1, content="socket.send(socket.recv())")
    
    request = Request('POST', body="3:::ping")
    transport.respond(request)
 
    request = Request('GET')
    response = transport.respond(request)

    expected = "3:::ping"
    actual = response.body.next()
    assert actual == expected, actual


attach_teardown(globals())
