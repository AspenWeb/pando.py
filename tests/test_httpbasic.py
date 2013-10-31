from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises, yield_fixture

from aspen.http.response import Response
from aspen.auth.httpbasic import inbound_responder

import base64

# convenience functions

def _auth_header(username, password):
    """return the value part of an Authorization: header for basic auth with the specified username and password"""
    return "Basic " + base64.b64encode(username + ":" + password)

# tests

@yield_fixture
def request_with(harness):
    def request_with(authfunc, auth_header):
        harness.website.flow.insert_after( inbound_responder(authfunc)
                                         , 'parse_environ_into_request'
                                          )
        return harness.simple( filepath=None
                             , run_through='_'
                             , want='response'
                             , HTTP_AUTHORIZATION=auth_header
                              )
    yield request_with

def test_good_works():
    request = _request_with(lambda u, p: u == "username" and p == "password", _auth_header("username", "password"))
    success = request.auth.authorized()
    assert success
    assert request.auth.username() == "username", request.auth.username()

def test_hard_passwords():
    for password in [ 'pass', 'username', ':password', ':password:','::::::' ]:
        request = _request_with(lambda u, p: u == "username" and p == password, _auth_header("username", password))
        success = request.auth.authorized()
        assert success
        assert request.auth.username() == "username", request.auth.username()

def test_no_auth():
    auth = lambda u, p: u == "username" and p == "password"
    response = raises(Response, _request_with, auth, None).value
    assert response.code == 401, response

def test_bad_fails():
    auth = lambda u, p: u == "username" and p == "password"
    response = raises(Response, _request_with, auth, _auth_header("username", "wrong password")).value
    assert response.code == 401, response

def test_wrong_auth():
    auth = lambda u, p: u == "username" and p == "password"
    response = raises(Response, _request_with, auth, "Wacky xxx").value
    assert response.code == 400, response

def test_malformed_password(request_with):
    auth = lambda u, p: u == "username" and p == "password"
    response = raises( Response
                     , request_with
                     , auth
                     , "Basic " + base64.b64encode("usernamepassword")
                      ).value
    assert response.code == 400, response
    response = raises(Response, request_with, auth, "Basic xxx").value
    assert response.code == 400, response
