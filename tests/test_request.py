from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from aspen import Response
from aspen.http.request import kick_against_goad, Request
from aspen.http.baseheaders import BaseHeaders
from aspen.testing import StubRequest
from aspen.testing.fsfix import teardown_function


def test_request_line_raw_works():
    request = StubRequest()
    actual = request.line.raw
    expected = u"GET / HTTP/1.1"
    assert actual == expected

def test_raw_is_raw():
    request = Request()
    expected = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    actual = request
    assert actual == expected

def test_blank_by_default():
    raises(AttributeError, lambda: Request().version)

def test_request_line_version_defaults_to_HTTP_1_1():
    request = StubRequest()
    actual = request.line.version.info
    expected = (1, 1)
    assert actual == expected

def test_request_line_version_raw_works():
    request = StubRequest()
    actual = request.line.version.raw
    expected = u"HTTP/1.1"
    assert actual == expected

def test_allow_default_method_is_GET():
    request = StubRequest()
    expected = u'GET'
    actual = request.line.method
    assert actual == expected

def test_allow_allows_allowed():
    request = StubRequest()
    expected = None
    actual = request.allow('GET')
    assert actual is expected

def test_allow_disallows_disallowed():
    request = StubRequest()
    expected = 405
    actual = raises(Response, request.allow, 'POST').value.code
    assert actual == expected

def test_allow_can_handle_lowercase():
    request = StubRequest()
    expected = 405
    actual = raises(Response, request.allow, 'post').value.code
    assert actual == expected

def test_methods_start_with_GET():
    request = StubRequest()
    expected = "GET"
    actual = request.line.method
    assert actual == expected

def test_methods_changing_changes():
    request = StubRequest()
    request.line.method = 'POST'
    expected = "POST"
    actual = request.line.method
    assert actual == expected

def test_is_xhr_false():
    request = StubRequest()
    assert not request.is_xhr()

def test_is_xhr_true():
    request = StubRequest()
    request.headers['X-Requested-With'] = 'XmlHttpRequest'
    assert request.is_xhr()

def test_is_xhr_is_case_insensitive():
    request = StubRequest()
    request.headers['X-Requested-With'] = 'xMLhTTPrEQUEST'
    assert request.is_xhr()


def test_headers_access_gets_a_value():
    headers = BaseHeaders(b"Foo: Bar")
    expected = b"Bar"
    actual = headers['Foo']
    assert actual == expected

def test_headers_access_gets_last_value():
    headers = BaseHeaders(b"Foo: Bar\r\nFoo: Baz")
    expected = b"Baz"
    actual = headers['Foo']
    assert actual == expected

def test_headers_access_is_case_insensitive():
    headers = BaseHeaders(b"Foo: Bar")
    expected = b"Bar"
    actual = headers['foo']
    assert actual == expected

def test_headers_dont_unicodify_cookie():
    headers = BaseHeaders(b"Cookie: somecookiedata")
    expected = b"somecookiedata"
    actual = headers[b'Cookie']
    assert actual == expected


# kick_against_goad

def test_goad_passes_method_through():
    environ = {}
    environ['REQUEST_METHOD'] = b'\xdead\xbeef'
    environ['SERVER_PROTOCOL'] = b''
    environ['wsgi.input'] = None

    expected = (b'\xdead\xbeef', b'', b'', b'', b'', None)
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_makes_franken_uri():
    environ = {}
    environ['REQUEST_METHOD'] = b''
    environ['SERVER_PROTOCOL'] = b''
    environ['PATH_INFO'] = b'/cheese'
    environ['QUERY_STRING'] = b'foo=bar'
    environ['wsgi.input'] = b''

    expected = ('', '/cheese?foo=bar', '', '', '', '')
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_passes_version_through():
    environ = {}
    environ['REQUEST_METHOD'] = b''
    environ['SERVER_PROTOCOL'] = b'\xdead\xbeef'
    environ['wsgi.input'] = None

    expected = (b'', b'', b'', b'\xdead\xbeef', b'', None)
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_makes_franken_headers():
    environ = {}
    environ['REQUEST_METHOD'] = b''
    environ['SERVER_PROTOCOL'] = b''
    environ['HTTP_FOO_BAR'] = b'baz=buz'
    environ['wsgi.input'] = b''

    expected = (b'', b'', b'', b'', b'FOO-BAR: baz=buz', b'')
    actual = kick_against_goad(environ)
    assert actual == expected

def test_goad_passes_body_through():
    environ = {}
    environ['REQUEST_METHOD'] = b''
    environ['SERVER_PROTOCOL'] = b''
    environ['wsgi.input'] = b'\xdead\xbeef'

    expected = (b'', b'', b'', b'', b'', b'\xdead\xbeef')
    actual = kick_against_goad(environ)
    assert actual == expected


def test_request_redirect_works_on_instance():
    request = Request()
    actual = raises(Response, request.redirect, '/').value.code
    assert actual == 302

def test_request_redirect_works_on_class():
    actual = raises(Response, Request.redirect, '/').value.code
    assert actual == 302

def test_request_redirect_code_is_settable():
    actual = raises(Response, Request.redirect, '/', code=8675309).value.code
    assert actual == 8675309

def test_request_redirect_permanent_convenience():
    actual = raises(Response, Request.redirect, '/', permanent=True).value.code
    assert actual == 301



