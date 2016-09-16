# coding: utf8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ipaddress import IPv4Network

from pytest import raises

from pando import Response
from pando.http.request import kick_against_goad, make_franken_uri, Request
from pando.http.baseheaders import BaseHeaders


def test_raw_is_raw():
    request = Request(None)
    expected = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    actual = str(request)
    assert actual == expected

def test_blank_by_default():
    raises(AttributeError, lambda: Request(None).version)

def test_request_line_version_defaults_to_HTTP_1_1(harness):
    request = harness.make_request()
    actual = request.line.version.info
    expected = (1, 1)
    assert actual == expected

def test_allow_default_method_is_GET(harness):
    request = harness.make_request()
    expected = b'GET'
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
    expected = b"GET"
    actual = request.line.method
    assert actual == expected

def test_methods_changing_changes(harness):
    request = harness.make_request()
    request.line.method = b'POST'
    expected = b"POST"
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
    headers = BaseHeaders([(b"Foo", b"Bar")])
    expected = b"Bar"
    actual = headers[b'Foo']
    assert actual == expected

def test_headers_access_gets_last_value():
    headers = BaseHeaders([(b"Foo", b"Bar"), (b"Foo", b"Baz")])
    expected = b"Baz"
    actual = headers[b'Foo']
    assert actual == expected

def test_headers_access_is_case_insensitive():
    headers = BaseHeaders({b"Foo": b"Bar"})
    expected = b"Bar"
    actual = headers[b'foo']
    assert actual == expected

def test_headers_dont_unicodify_cookie():
    headers = BaseHeaders({b"Cookie": b"somecookiedata"})
    expected = b"somecookiedata"
    actual = headers[b'Cookie']
    assert actual == expected

def test_baseheaders_loads_cookies_as_str():
    headers = BaseHeaders({b"Cookie": b"key=value"})
    assert headers.cookie[str('key')].value == str('value')


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
    assert request.path.decoded == '/'

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


# make_franken_uri

def test_make_franken_uri_works_with_properly_escaped_uri():
    expected = b'/%C2%B5?%C2%B5=%C2%B5&foo=bar'
    actual = make_franken_uri(b'/%C2%B5', b'%C2%B5=%C2%B5&foo=bar')
    assert actual == expected


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


# from_wsgi

def test_from_wsgi_tolerates_non_ascii_environ(harness):
    environ = {}
    environ[b'REQUEST_METHOD'] = b'GET'
    environ[b'HTTP_HOST'] = 'µ.example.com'.encode('utf8')
    environ[b'SERVER_PROTOCOL'] = b'HTTP/1.0'
    environ[b'wsgi.input'] = None
    environ[b'HTTP_\xff'] = b'\xdead\xbeef'
    environ['HTTP_À'.encode('utf8')] = 'µ'.encode('utf8')
    environ[b'PATH_INFO'] = '/µ'.encode('utf8')
    environ[b'QUERY_STRING'] = 'µ=µ'.encode('utf8')
    request = Request.from_wsgi(harness.client.website, environ)
    assert request.line.uri == b'/%C2%B5?%C2%B5=%C2%B5'
    headers = request.headers
    assert headers[b'Host'] == b'\xc2\xb5.example.com'
    assert headers[b'\xff'] is environ[b'HTTP_\xff']
    assert headers['À'.encode('utf8')] == 'µ'.encode('utf8')

def test_from_wsgi_tolerates_unicode_environ(harness):
    environ = {}
    environ['REQUEST_METHOD'] = 'GET'
    environ['HTTP_HOST'] = 'µ.example.com'.encode('utf8').decode('latin1')
    environ['SERVER_PROTOCOL'] = 'HTTP/1.0'
    environ['wsgi.input'] = None
    environ[b'HTTP_\xff'] = b'\xdead\xbeef'
    environ['HTTP_À'] = 'µ'.encode('utf8').decode('latin1')
    environ['PATH_INFO'] = '/µ'.encode('utf8').decode('latin1')
    environ['QUERY_STRING'] = 'µ=µ'.encode('utf8').decode('latin1')
    request = Request.from_wsgi(harness.client.website, environ)
    assert request.line.uri == b'/%C2%B5?%C2%B5=%C2%B5'
    headers = request.headers
    assert headers[b'Host'] == b'\xc2\xb5.example.com'
    assert headers[b'\xff'] is environ[b'HTTP_\xff']
    assert headers['À'.encode('latin1')] == 'µ'.encode('utf8')


# source

def request(harness, forwarded_for, source, **kw):
    harness.client.hydrate_website(trusted_proxies=[
        [IPv4Network('10.0.0.0/8')],
        [IPv4Network('141.101.64.0/18')],
    ])
    kw['HTTP_X_FORWARDED_FOR'] = forwarded_for
    kw['REMOTE_ADDR'] = source
    kw.setdefault('return_after', 'parse_environ_into_request')
    kw.setdefault('want', 'request')
    return harness.client.GET('/', **kw)

def test_request_source_with_invalid_header_from_trusted_proxy(harness):
    r = request(harness, b'f\xc3\xa9e, \t bar', b'10.0.0.1')
    assert str(r.source) == '10.0.0.1'
    assert r.bypasses_proxy is True

def test_request_source_with_invalid_header_from_untrusted_proxy(harness):
    r = request(harness, b'f\xc3\xa9e, \tbar', b'8.8.8.8')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is True

def test_request_source_with_valid_headers_from_trusted_proxies(harness):
    r = request(harness, b'8.8.8.8,141.101.69.139', b'10.0.0.1')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is False
    r = request(harness, b'8.8.8.8', b'10.0.0.2')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is True

def test_request_source_with_valid_headers_from_untrusted_proxies(harness):
    # 8.8.8.8 claims that the request came from 0.0.0.0, but we don't trust 8.8.8.8
    r = request(harness, b'0.0.0.0, 8.8.8.8,141.101.69.140', b'10.0.0.1')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is False
    r = request(harness, b'0.0.0.0, 8.8.8.8', b'10.0.0.1')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is True

def test_request_source_with_forged_headers_from_untrusted_client(harness):
    # 8.8.8.8 claims that the request came from a trusted proxy, but we don't trust 8.8.8.8
    r = request(harness, b'0.0.0.0,141.101.69.141, 8.8.8.8,141.101.69.142', b'10.0.0.1')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is False
    r = request(harness, b'0.0.0.0, 141.101.69.143, 8.8.8.8', b'10.0.0.1')
    assert str(r.source) == '8.8.8.8'
    assert r.bypasses_proxy is True

def test_request_source_is_cached(harness):
    r = request(harness, b'1.1.1.1', b'10.0.0.1')
    src1 = r.source
    src2 = r.source
    assert src1 is src2
