from aspen import Response
from aspen.http.mapping import Mapping
from aspen.http.request import Request
from aspen.tests import assert_raises
from diesel.protocols.http import HttpHeaders, HttpRequest

def DieselReq():
    diesel_request = HttpRequest('GET', '/', 'HTTP/1.1')
    diesel_request.headers = HttpHeaders(Host='localhost') # else 400 in hydrate
    return diesel_request

def make_request():
    return Request.from_diesel(DieselReq())
    

def test_blank_by_default():
    assert_raises(AttributeError, lambda: Request().version)

def test_hydrate_can_hydrate():
    request = make_request()
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

def test_mappings_minimally_work():
    request = make_request()
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

def test_allow_default_method_is_GET():
    request = make_request()
    expected = 'GET'
    actual = request.method
    assert actual == expected, actual

def test_allow_allows_allowed():
    request = make_request()
    expected = None
    actual = request.allow('GET')
    assert actual is expected, actual
    
def test_allow_disallows_disallowed():
    request = make_request()
    expected = 405
    actual = assert_raises(Response, request.allow, 'POST').code
    assert actual == expected, actual
    
def test_allow_can_handle_lowercase():
    request = make_request()
    expected = 405
    actual = assert_raises(Response, request.allow, 'post').code
    assert actual == expected, actual
    
