from aspen.http import Response
from aspen.tests import assert_raises
from aspen.tests.fsfix import attach_teardown
from diesel.protocols.http import HttpHeaders, HttpRequest


def DieselReq():
    diesel_request = HttpRequest('GET', '/', 'HTTP/1.1')
    diesel_request.headers = HttpHeaders(Host='localhost') # else 400
    return diesel_request

def test_to_diesel_raises_AttributeError():
    # This is because _to_diesel actually pushes bits, but we have no loop
    response = Response()
    assert_raises(AttributeError, response._to_diesel, DieselReq)


attach_teardown(globals())
