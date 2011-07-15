from collections import deque

from aspen import Response
from aspen.http.request import Request
from aspen.sockets.transport import XHRPollingTransport
from aspen.sockets.message import Message
from aspen.tests.test_sockets_socket import make_socket
from aspen.tests.fsfix import attach_teardown, mk


def make_transport(state=0):
    mk(('echo.sock', ''))
    socket = make_socket()
    transport = XHRPollingTransport(socket)
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
    transport.socket.outgoing.push(Message.from_bytes("3:::Greetings, program!"))
    
    request = Request('GET')
    response = transport.respond(request)
   
    expected = response.body
    actual = ''
    assert actual == expected, actual
    

attach_teardown(globals())
