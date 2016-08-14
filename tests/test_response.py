from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from pando import Response
from pando.exceptions import CRLFInjection


def test_response_is_a_wsgi_callable():
    response = Response(body=b"Greetings, program!")
    def start_response(status, headers):
        pass
    expected = [b"Greetings, program!"]
    actual = list(response({}, start_response).body)
    assert actual == expected

def test_response_wsgi_status_is_not_based_on_str_method():
    class CustomResponse(Response):
        __str__ = lambda self: 'not a valid HTTP status line'
    response = CustomResponse()
    def start_response(status, headers):
        assert status == '200 OK'
    response({}, start_response)

def test_response_body_can_be_bytestring():
    response = Response(body=b"Greetings, program!")
    expected = b"Greetings, program!"
    actual = response.body
    assert actual == expected

def test_response_body_as_bytestring_results_in_an_iterable():
    response = Response(body=b"Greetings, program!")
    def start_response(status, headers):
        pass
    expected = [b"Greetings, program!"]
    actual = list(response({}, start_response).body)
    assert actual == expected

def test_response_body_can_be_iterable():
    response = Response(body=["Greetings, ", "program!"])
    expected = ["Greetings, ", "program!"]
    actual = response.body
    assert actual == expected

def test_response_body_as_iterable_comes_through_untouched():
    response = Response(body=[b"Greetings, ", b"program!"])
    def start_response(status, headers):
        pass
    expected = [b"Greetings, ", b"program!"]
    actual = list(response({}, start_response).body)
    assert actual == expected

def test_response_body_can_be_unicode():
    try:
        Response(body='Greetings, program!')
    except:
        assert False, 'expecting no error'

def test_response_headers_protect_against_crlf_injection():
    response = Response()
    def inject():
        response.headers[b'Location'] = b'foo\r\nbar'
    raises(CRLFInjection, inject)
