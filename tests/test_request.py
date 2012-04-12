from aspen import Response
from aspen.http.mapping import Mapping
from aspen.http.request import kick_against_goad, Method, Request
from aspen.http.baseheaders import BaseHeaders
from aspen.testing import assert_raises, StubRequest
from aspen.testing.fsfix import attach_teardown


def test_request_line_version_raw_works():
    request = StubRequest()
    actual = request.line.raw
    expected = u"GET / HTTP/1.1"
    assert actual == expected, actual

def test_raw_is_raw():
    request = Request()
    expected = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    actual = request
    assert actual == expected, actual

def test_blank_by_default():
    assert_raises(AttributeError, lambda: Request().version)

def test_request_line_version_defaults_to_HTTP_1_1():
    request = StubRequest()
    actual = request.line.version.info
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


def test_headers_access_gets_a_value():
    headers = BaseHeaders("Foo: Bar")
    expected = "Bar"
    actual = headers['Foo']
    assert actual == expected, actual
    
def test_headers_access_gets_last_value():
    headers = BaseHeaders("Foo: Bar\r\nFoo: Baz")
    expected = "Baz"
    actual = headers['Foo']
    assert actual == expected, actual
    
def test_headers_access_is_case_insensitive():
    headers = BaseHeaders("Foo: Bar")
    expected = "Bar"
    actual = headers['foo']
    assert actual == expected, actual
    

# kick_against_goad

def test_goad_passes_method_through():
    environ = {}
    environ['REQUEST_METHOD'] = '\xdead\xbeef'
    environ['SERVER_PROTOCOL'] = ''
    environ['wsgi.input'] = None

    expected = ('\xdead\xbeef', '', '', '', None)
    actual = kick_against_goad(environ)
    assert actual == expected, actual

def test_goad_makes_franken_uri():
    environ = {}
    environ['REQUEST_METHOD'] = ''
    environ['SERVER_PROTOCOL'] = ''
    environ['PATH_INFO'] = '/cheese'
    environ['QUERY_STRING'] = 'foo=bar'
    environ['wsgi.input'] = ''

    expected = ('', '/cheese?foo=bar', '', '', '')
    actual = kick_against_goad(environ)
    assert actual == expected, actual

def test_goad_passes_version_through():
    environ = {}
    environ['REQUEST_METHOD'] = ''
    environ['SERVER_PROTOCOL'] = '\xdead\xbeef'
    environ['wsgi.input'] = None

    expected = ('', '', '\xdead\xbeef', '', None)
    actual = kick_against_goad(environ)
    assert actual == expected, actual

def test_goad_makes_franken_headers():
    environ = {}
    environ['REQUEST_METHOD'] = ''
    environ['SERVER_PROTOCOL'] = ''
    environ['HTTP_FOO_BAR'] = 'baz=buz'
    environ['wsgi.input'] = ''

    expected = ('', '', '', 'FOO-BAR: baz=buz', '')
    actual = kick_against_goad(environ)
    assert actual == expected, actual

def test_goad_passes_body_through():
    environ = {}
    environ['REQUEST_METHOD'] = ''
    environ['SERVER_PROTOCOL'] = ''
    environ['wsgi.input'] = '\xdead\xbeef'

    expected = ('', '', '', '', '\xdead\xbeef')
    actual = kick_against_goad(environ)
    assert actual == expected, actual


attach_teardown(globals())
