from aspen import Response
from aspen.http.mapping import Mapping
from aspen.http.request import Request, Method
from aspen.http.baseheaders import BaseHeaders
from aspen.testing import assert_raises, StubRequest
from aspen.testing.fsfix import attach_teardown



def test_method_works():
    method = Method("GET")
    actual = method
    expected = u"GET"
    assert actual == expected, actual

def test_method_is_unicode():
    method = Method("GET")
    actual = method
    assert isinstance(actual, unicode), actual.__class__

def test_method_raw_works():
    method = Method("GET")
    actual = method.raw
    expected = "GET"
    assert actual == expected, actual

def test_method_raw_is_bytestring():
    method = Method("GET")
    actual = method.raw
    assert isinstance(actual, str), actual.__class__




def test_request_line_version_raw_works():
    request = StubRequest()
    actual = request.line.raw
    expected = u"GET / HTTP/1.1"
    assert actual == expected, actual

def test_raw_is_raw():
    request = Request()
    expected = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    actual = request.raw
    assert actual == expected, actual

def test_blank_by_default():
    assert_raises(AttributeError, lambda: Request().version)

def test_request_line_version_defaults_to_HTTP_1_1():
    request = StubRequest()
    actual = request.line.version
    expected = (1, 1)
    assert actual == expected, actual

def test_request_line_version_raw_works():
    request = StubRequest()
    actual = request.line.version.raw
    expected = u"HTTP/1.1"
    assert actual == expected, actual

def test_allow_default_method_is_GET():
    request = StubRequest()
    expected = u'GET'
    actual = request.line.method
    assert actual == expected, actual

def test_allow_allows_allowed():
    request = StubRequest()
    expected = None
    actual = request.allow('GET')
    assert actual is expected, actual
    
def test_allow_disallows_disallowed():
    request = StubRequest()
    expected = 405
    actual = assert_raises(Response, request.allow, 'POST').code
    assert actual == expected, actual
    
def test_allow_can_handle_lowercase():
    request = StubRequest()
    expected = 405
    actual = assert_raises(Response, request.allow, 'post').code
    assert actual == expected, actual

def test_methods_start_with_GET():
    request = StubRequest()
    expected = "GET"
    actual = request.line.method
    assert actual == expected, actual

def test_methods_changing_changes():
    request = StubRequest()
    request.line.method = 'POST'
    expected = "POST"
    actual = request.line.method
    assert actual == expected, actual

def test_is_xhr_false():
    request = StubRequest()
    assert not request.is_xhr()
    
def test_is_xhr_true():
    request = StubRequest()
    request.headers.set('X-Requested-With', 'XmlHttpRequest')
    assert request.is_xhr()
    
def test_is_xhr_is_case_insensitive():
    request = StubRequest()
    request.headers.set('X-Requested-With', 'xMLhTTPrEQUEST')
    assert request.is_xhr()


def test_headers_one_gets_a_value():
    headers = BaseHeaders("Foo: Bar")
    expected = "Bar"
    actual = headers.one('Foo')
    assert actual == expected, actual
    
def test_headers_one_gets_first_value():
    headers = BaseHeaders("Foo: Bar\r\nFoo: Baz")
    expected = "Bar"
    actual = headers.one('Foo')
    assert actual == expected, actual
    
def test_headers_one_is_case_insensitive():
    headers = BaseHeaders("Foo: Bar")
    expected = "Bar"
    actual = headers.one('foo')
    assert actual == expected, actual
    

attach_teardown(globals())
