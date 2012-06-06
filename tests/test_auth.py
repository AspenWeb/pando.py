

from aspen.http.response import Response
from aspen.testing import assert_raises, StubRequest
from aspen.auth import httpbasic 

import base64

# convenience functions

def _auth_header(username, password):
    """return the value part of an Authorization: header for basic auth with the specified username and password"""
    return "Basic " + base64.b64encode(username + ":" + password)


# tests

def test_good_works():
    request = StubRequest()
    auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == "password")
    request.headers['Authorization'] = _auth_header("username", "password")
    success, response = auth.authorized(request)
    assert success, response

def test_hard_passwords():
    request = StubRequest()
    for password in [ 'pass', 'username', ':password', ':password:','::::::' ]:
        auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == password)
        request.headers['Authorization'] = _auth_header("username", password)
        success, response = auth.authorized(request)
        assert success, response

def test_no_auth():
    request = StubRequest()
    auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == "password")
    success, response = auth.authorized(request)
    assert response.code == 401, response

def test_bad_fails():
    request = StubRequest()
    auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == "password")
    request.headers['Authorization'] = _auth_header("username", "wrong password")
    success, response = auth.authorized(request)
    assert response.code == 401, response
    
def test_wrong_auth():
    request = StubRequest()
    auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == "password")
    request.headers['Authorization'] = "Wacky xxxx"
    success, response = auth.authorized(request)
    assert response.code == 400, response

def test_malformed_password():
    request = StubRequest()
    auth = httpbasic.BasicAuth(lambda u, p: u == "username" and p == "password")
    request.headers['Authorization'] = "Basic xxxx"
    success, response = auth.authorized(request)
    assert response.code == 400, response


