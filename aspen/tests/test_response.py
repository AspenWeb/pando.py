from aspen import Response
from aspen.tests import assert_raises
from aspen.tests.fsfix import attach_teardown


def test_response_is_a_wsgi_callable():
    response = Response(body="Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = response({}, start_response)
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
    actual = response({}, start_response)
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
    actual = response({}, start_response)
    assert actual == expected, actual

def test_response_body_cannot_be_unicode():
    exc = assert_raises(TypeError, Response, body=u"Greetings, program!")


attach_teardown(globals())
