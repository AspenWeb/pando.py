from aspen.http import Mapping, Request
from aspen.tests import assert_raises
from diesel.protocols.http import HttpHeaders, HttpRequest

def DieselReq():
    diesel_request = HttpRequest('GET', '/', 'HTTP/1.1')
    diesel_request.headers = HttpHeaders(Host='localhost') # else 400 in hydrate
    return diesel_request

def test_blank_by_default():
    assert_raises(AttributeError, lambda: Request().version)

def test_hydrate_can_hydrate():
    request = Request.from_diesel(DieselReq())
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

def test_mappings_minimally_work():
    request = Request.from_diesel(DieselReq())
    actual = request.version
    expected = 'HTTP/1.1'
    assert actual == expected, actual

