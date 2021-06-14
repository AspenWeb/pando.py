import os
from pytest import raises

from pando import Response
from pando.exceptions import CRLFInjection
from pando.website import THE_PAST


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
    assert response.body == b"Greetings, program!"
    assert response.text == "Greetings, program!"

def test_response_body_can_be_iterable():
    response = Response(body=["Greetings, ", "program!"])
    assert response.body == ["Greetings, ", "program!"]
    assert response.text == "Greetings, program!"

def test_response_body_as_iterable_comes_through_untouched():
    response = Response(body=[b"Greetings, ", b"program!"])

    def start_response(status, headers):
        pass

    expected = [b"Greetings, ", b"program!"]
    actual = list(response.to_wsgi({}, start_response, 'utf8').body)
    assert actual == expected

def test_response_body_can_be_unicode():
    response = Response(body="Greetings, program!")
    assert response.body == "Greetings, program!"
    assert response.text == "Greetings, program!"

def test_wsgi_response_headers_are_str():
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
    response.headers.cookie['foo'] = 'bar'

    def start_response(status, headers):
        assert headers[0][0] == 'Set-Cookie'
        assert headers[0][1].startswith('foo=bar')

    response.to_wsgi({}, start_response, 'utf8')

def test_response_set_cookie(harness):
    response = Response()
    response.website = harness.client.website
    response.set_cookie('foo', 'bar')

    def start_response(status, headers):
        assert headers[0][0] == 'Set-Cookie'
        assert headers[0][1].startswith('foo=bar;')

    response.to_wsgi({}, start_response, 'utf8')

def test_response_erase_cookie(harness):
    response = Response()
    response.website = harness.client.website
    response.erase_cookie('foo')

    def start_response(status, headers):
        assert headers[0][0] == 'Set-Cookie'
        assert headers[0][1] == f'foo=""; expires={THE_PAST}; HttpOnly; Path=/; SameSite=lax'

    response.to_wsgi({}, start_response, 'utf8')

def test_set_whence_raised_works():
    try:
        raise Response(200)
    except Response as r:
        assert r.whence_raised == (None, None)
        r.set_whence_raised()
        assert r.whence_raised[0] == 'tests' + os.sep + 'test_response.py'
        assert isinstance(r.whence_raised[1], int)

def test_response_render(harness):
    harness.fs.project.mk(('refresh.spt', """
        [---]
        if url:
            refresh_header = b'%i;url=%s' % (state.get('interval', 0), response.encode_url(url))
        else:
            refresh_header = b'%i' % interval
        response.headers[b'Refresh'] = refresh_header
        [---] text/plain
        Processing…
    """))
    response = Response()
    state = {
        'website': harness.client.website,
        'response': response,
        'accept_header': '*/*',
    }
    response.render(harness.fs.project.root + '/refresh.spt', state, interval=0, url='')
    assert response.text == "Processing…\n"
