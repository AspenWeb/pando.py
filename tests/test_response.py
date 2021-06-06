import os
from pytest import raises

from pando import Response
from pando.exceptions import CRLFInjection


def test_response_to_wsgi():
    response = Response(body=b"Greetings, program!")

    def start_response(status, headers):
        pass

    expected = [b"Greetings, program!"]
    actual = list(response.to_wsgi({}, start_response, 'utf8').body)
    assert actual == expected

def test_response_wsgi_status_is_not_based_on_str_method():
    class CustomResponse(Response):
        def __str__(self):
            return 'not a valid HTTP status line'

    response = CustomResponse()

    def start_response(status, headers):
        assert status == '200 OK'

    response.to_wsgi({}, start_response, 'utf8')

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
    actual = list(response.to_wsgi({}, start_response, 'utf8').body)
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
    actual = list(response.to_wsgi({}, start_response, 'utf8').body)
    assert actual == expected

def test_response_body_can_be_unicode():
    try:
        Response(body='Greetings, program!')
    except Exception:
        assert False, 'expecting no error'

def test_response_headers_are_str():
    response = Response()
    response.headers[b'Location'] = b'somewhere'

    def start_response(status, headers):
        assert isinstance(headers[0][0], str)
        assert isinstance(headers[0][1], str)

    response.to_wsgi({}, start_response, 'utf8')

def test_response_headers_protect_against_crlf_injection():
    response = Response()

    def inject():
        response.headers[b'Location'] = b'foo\r\nbar'

    raises(CRLFInjection, inject)

def test_response_cookie():
    response = Response()
    response.headers.cookie[str('foo')] = str('bar')

    def start_response(status, headers):
        assert headers[0][0] == str('Set-Cookie')
        assert headers[0][1].startswith(str('foo=bar'))

    response.to_wsgi({}, start_response, 'utf8')

def test_set_whence_raised_works():
    try:
        raise Response(200)
    except Response as r:
        assert r.whence_raised == (None, None)
        r.set_whence_raised()
        assert r.whence_raised[0] == 'tests' + os.sep + 'test_response.py'
        assert isinstance(r.whence_raised[1], int)
