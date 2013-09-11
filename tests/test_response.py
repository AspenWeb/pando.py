from aspen import Response
from aspen.testing import assert_raises
from aspen.testing.fsfix import attach_teardown
from aspen.exceptions import CRLFInjection


def test_response_is_a_wsgi_callable():
    response = Response(body="Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = response({}, start_response).body
    assert actual == expected, actual

def test_response_body_can_be_bytestring():
    response = Response(body="Greetings, program!")
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual

def test_response_body_as_bytestring_results_in_list():
    response = Response(body="Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = response({}, start_response).body
    assert actual == expected, actual

def test_response_body_can_be_iterable():
    response = Response(body=["Greetings, ", "program!"])
    expected = ["Greetings, ", "program!"]
    actual = response.body
    assert actual == expected, actual

def test_response_body_as_iterable_comes_through_untouched():
    response = Response(body=["Greetings, ", "program!"])
    def start_response(status, headers):
        pass
    expected = ["Greetings, ", "program!"]
    actual = response({}, start_response).body
    assert actual == expected, actual

def test_response_body_cannot_be_unicode():
    exc = assert_raises(TypeError, Response, body=u"Greetings, program!")

def test_response_headers_protect_against_crlf_injection():
    response = Response()
    def inject():
        response.headers['Location'] = 'foo\r\nbar'
    assert_raises(CRLFInjection, inject)


attach_teardown(globals())
