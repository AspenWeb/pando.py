from aspen import Response
from aspen.http.mapping import Mapping
from aspen.http.request import Request
from aspen.http.headers import Headers
from aspen.testing import assert_raises, StubRequest
from aspen.testing.fsfix import attach_teardown


def test_blank_by_default():
    assert_raises(AttributeError, lambda: Request().version)

def test_hydrate_can_hydrate():
    request = StubRequest()
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

def test_mappings_minimally_work():
    request = StubRequest()
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

def test_allow_default_method_is_GET():
    request = StubRequest()
    expected = 'GET'
    actual = request.method
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
    assert not request.OPTIONS
    assert request.GET
    assert not request.HEAD
    assert not request.POST
    assert not request.PUT
    assert not request.DELETE
    assert not request.TRACE
    assert not request.CONNECT

def test_methods_changing_changes():
    request = StubRequest()
    request.method = 'POST'
    assert not request.OPTIONS
    assert not request.GET
    assert not request.HEAD
    assert request.POST
    assert not request.PUT
    assert not request.DELETE
    assert not request.TRACE
    assert not request.CONNECT

def test_is_xhr_false():
    request = StubRequest()
    assert not request.is_xhr
    
def test_is_xhr_true():
    request = StubRequest()
    request.headers.set('X-Requested-With', 'XmlHttpRequest')
    assert request.is_xhr
    
def test_is_xhr_is_case_insensitive():
    request = StubRequest()
    request.headers.set('X-Requested-With', 'xMLhTTPrEQUEST')
    assert request.is_xhr


def test_headers_one_gets_a_value():
    headers = Headers("Foo: Bar")
    expected = "Bar"
    actual = headers.one('Foo')
    assert actual == expected, actual
    
def test_headers_one_gets_first_value():
    headers = Headers("Foo: Bar\r\nFoo: Baz")
    expected = "Bar"
    actual = headers.one('Foo')
    assert actual == expected, actual
    
def test_headers_one_is_case_insensitive():
    headers = Headers("Foo: Bar")
    expected = "Bar"
    actual = headers.one('foo')
    assert actual == expected, actual
    

attach_teardown(globals())
