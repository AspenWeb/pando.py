from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import Response
from aspen.testing import assert_raises
from aspen.testing.fsfix import attach_teardown
from aspen.exceptions import CRLFInjection


def test_response_is_a_wsgi_callable():
    response = Response(body=b"Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = list(response({}, start_response).body)
    assert actual == expected, actual

def test_response_body_can_be_bytestring():
    response = Response(body=b"Greetings, program!")
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual

def test_response_body_as_bytestring_results_in_an_iterable():
    response = Response(body=b"Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = list(response({}, start_response).body)
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
    actual = list(response({}, start_response).body)
    assert actual == expected, actual

def test_response_body_can_be_unicode():
    try:
        Response(body=u'Greetings, program!')
    except:
        assert False, 'expecting no error'

def test_response_headers_protect_against_crlf_injection():
    response = Response()
    def inject():
        response.headers['Location'] = 'foo\r\nbar'
    assert_raises(CRLFInjection, inject)


attach_teardown(globals())
