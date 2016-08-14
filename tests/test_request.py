from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from pando import Response
from pando.http.request import make_franken_headers, kick_against_goad, Request
from pando.http.baseheaders import BaseHeaders
from pando.exceptions import MalformedHeader


def test_request_line_raw_works(harness):
    request = harness.make_request()
    actual = request.line.raw
    expected = "GET / HTTP/1.1"
    assert actual == expected

def test_raw_is_raw():
    request = Request()
    expected = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    actual = str(request)
    assert actual == expected

def test_blank_by_default():
    raises(AttributeError, lambda: Request().version)

def test_request_line_version_defaults_to_HTTP_1_1(harness):
    request = harness.make_request()
    actual = request.line.version.info
    expected = (1, 1)
    assert actual == expected

def test_request_line_version_raw_works(harness):
    request = harness.make_request()
    actual = request.line.version.raw
    expected = "HTTP/1.1"
    assert actual == expected

def test_allow_default_method_is_GET(harness):
    request = harness.make_request()
    expected = 'GET'
    actual = request.line.method
    assert actual == expected

def test_allow_allows_allowed(harness):
    request = harness.make_request()
    expected = None
    actual = request.allow('GET')
    assert actual is expected

def test_allow_disallows_disallowed(harness):
    request = harness.make_request()
    expected = 405
    actual = raises(Response, request.allow, 'POST').value.code
    assert actual == expected

def test_allow_can_handle_lowercase(harness):
    request = harness.make_request()
    expected = 405
    actual = raises(Response, request.allow, 'post').value.code
    assert actual == expected

def test_methods_start_with_GET(harness):
    request = harness.make_request()
    expected = "GET"
    actual = request.line.method
    assert actual == expected

def test_methods_changing_changes(harness):
    request = harness.make_request()
    request.line.method = 'POST'
    expected = "POST"
    actual = request.line.method
    assert actual == expected

def test_is_xhr_false(harness):
    request = harness.make_request()
    assert not request.is_xhr()

def test_is_xhr_true(harness):
    request = harness.make_request()
    request.headers[b'X-Requested-With'] = b'XmlHttpRequest'
    assert request.is_xhr()

def test_is_xhr_is_case_insensitive(harness):
    request = harness.make_request()
    request.headers[b'X-Requested-With'] = b'xMLhTTPrEQUEST'
    assert request.is_xhr()


def test_headers_access_gets_a_value():
    headers = BaseHeaders(b"Foo: Bar")
    expected = b"Bar"
    actual = headers[b'Foo']
    assert actual == expected

def test_headers_access_gets_last_value():
    headers = BaseHeaders(b"Foo: Bar\r\nFoo: Baz")
    expected = b"Baz"
    actual = headers[b'Foo']
    assert actual == expected

def test_headers_access_is_case_insensitive():
    headers = BaseHeaders(b"Foo: Bar")
    expected = b"Bar"
    actual = headers[b'foo']
    assert actual == expected

def test_headers_dont_unicodify_cookie():
    headers = BaseHeaders(b"Cookie: somecookiedata")
    expected = b"somecookiedata"
    actual = headers[b'Cookie']
    assert actual == expected

def test_headers_handle_no_colon():
    raises(MalformedHeader, BaseHeaders, b"Foo Bar")

def test_headers_handle_bad_spaces():
    raises(MalformedHeader, BaseHeaders, b"Foo : Bar")


# aliases

def test_method_alias_is_readable(harness):
    request = harness.make_request()
    assert request.method == 'GET'

def test_method_alias_is_read_only(harness):
    request = harness.make_request()
    with raises(AttributeError):
        request.method = 'foo'

def test_path_alias_is_readable(harness):
    request = harness.make_request()
    assert request.path.raw == '/'

def test_path_alias_is_read_only(harness):
    request = harness.make_request()
    with raises(AttributeError):
        request.path = 'foo'

def test_qs_alias_is_readable(harness):
    request = harness.make_request()
    assert request.qs == {}

def test_qs_alias_is_read_only(harness):
    request = harness.make_request()
    with raises(AttributeError):
        request.qs = 'foo'

def test_cookie_alias_is_readable(harness):
    request = harness.make_request()
    assert list(request.cookie.values()) == []

def test_cookie_alias_is_read_only(harness):
    request = harness.make_request()
    with raises(AttributeError):
        request.cookie = 'foo'


# kick_against_goad

def test_goad_passes_method_through():
    environ = {}
    environ[b'REQUEST_METHOD'] = b'\xdead\xbeef'
    environ[b'SERVER_PROTOCOL'] = b''
    environ[b'wsgi.input'] = None

    expected = (b'\xdead\xbeef', b'', b'', b'', {}, None)
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_makes_franken_uri():
    environ = {}
    environ[b'REQUEST_METHOD'] = b''
    environ[b'SERVER_PROTOCOL'] = b''
    environ[b'PATH_INFO'] = b'/cheese'
    environ[b'QUERY_STRING'] = b'foo=bar'
    environ[b'wsgi.input'] = b''

    expected = (b'', b'/cheese?foo=bar', b'', b'', {}, b'')
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_passes_version_through():
    environ = {}
    environ[b'REQUEST_METHOD'] = b''
    environ[b'SERVER_PROTOCOL'] = b'\xdead\xbeef'
    environ[b'wsgi.input'] = None

    expected = (b'', b'', b'', b'\xdead\xbeef', {}, None)
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_makes_franken_headers():
    environ = {}
    environ[b'REQUEST_METHOD'] = b''
    environ[b'SERVER_PROTOCOL'] = b''
    environ[b'HTTP_FOO_BAR'] = b'baz=buz'
    environ[b'wsgi.input'] = b''

    expected = (b'', b'', b'', b'', {b'FOO-BAR': b'baz=buz'}, b'')
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_passes_body_through():
    environ = {}
    environ[b'REQUEST_METHOD'] = b''
    environ[b'SERVER_PROTOCOL'] = b''
    environ[b'wsgi.input'] = b'\xdead\xbeef'

    expected = (b'', b'', b'', b'', {}, b'\xdead\xbeef')
    actual = kick_against_goad(environ)
    assert actual == expected


def test_can_make_franken_headers_from_non_ascii_values():
    actual = make_franken_headers({b'HTTP_FOO_BAR': b'\xdead\xbeef'})
    assert actual == {b'FOO-BAR': b'\xdead\xbeef'}
