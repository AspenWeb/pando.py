from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises, yield_fixture

from aspen.http.response import Response
from aspen.auth.httpdigest import inbound_responder, digest

import base64

# convenience functions

def _auth_func(username, password):
    def _(user, realm):
        if user != username:
            raise KeyError
        return digest(':'.join([username, realm, password]))
    return _

def _auth_header(username, password):
    """return the value part of an Authorization: header for basic auth with the specified username and password"""
    return "Basic " + base64.b64encode(username + ":" + password)

def _auth_headers(response):
    wwwauth = response.headers['WWW-Authenticate']
    assert wwwauth.startswith('Digest')
    assert wwwauth.endswith('"')
    keyvals = wwwauth[len('Digest '):-1].split('",')
    return dict([kval.strip().split('="')  for kval in keyvals])


def _digest_auth_for(headers, username, password):
    fields = { 'qop': 'auth',
               'uri': '/',
               'nc':'00000001',
               'cnonce':'FFFFFFFF',
               'username' : username
             }
    for k in [ 'realm', 'nonce', 'opaque' ]:
        fields[k] = headers[k]
    HA1 = digest( username + ':' + fields['realm'] + ':' + password )
    HA2 = digest( 'GET:' + fields['uri'] )
    fields['response'] = digest( ':'.join([ HA1, fields['nonce'], fields['nc'], fields['cnonce'], fields['qop'], HA2 ]))
    return "Digest " + ','.join([ '%s="%s"' % (k, v) for k, v in fields.items() ])

@yield_fixture
def request_with(harness):
    def request_with(auth_header, inbound_auther):
        harness.website.flow.insert_after( inbound_auther
                                         , 'parse_environ_into_request'
                                          )
        return harness.simple( filepath=None
                             , run_through='httpdigest_inbound_responder'
                             , want='request'
                             , HTTP_AUTHORIZATION=auth_header
                              )
    yield request_with


# tests

def test_good_works(request_with):
    # once to get a WWW-Authenticate header
    auth_func = _auth_func("username", "password")
    auther = inbound_responder(auth_func, realm="testrealm@host.com") 
    response = raises(Response, request_with, '', auther).value
    # do something with the header
    auth_headers = _auth_headers(response)
    http_authorization = _digest_auth_for(auth_headers, "username", "password")
    request = request_with(http_authorization, auther)
    assert request.auth.authorized()
    assert request.auth.username() == "username"

#def test_hard_passwords():
#    for password in [ 'pass', 'username', ':password', ':password:','::::::' ]:
#        request = _request_with(_auth_func("username", "password"), _auth_header("username", "password"))
#        success = request.auth.authorized()
#        assert success
#        assert request.auth.username() == "username", request.auth.username()

def test_bad_fails(request_with):
    # once to get a WWW-Authenticate header
    auther = inbound_responder(_auth_func("username", "password"), realm="testrealm@host.com")
    response = raises(Response, request_with, '', auther).value
    # do something with the header
    auth_headers = _auth_headers(response)
    http_authorization = _digest_auth_for(auth_headers, "username", "badpassword")
    response = raises(Response, request_with, http_authorization, auther).value
    assert response.code == 401
    assert not response.request.auth.authorized()

def test_no_auth(request_with):
    auth = lambda u, p: u == "username" and p == "password"
    auther = inbound_responder(auth, realm="testrealm@host.com") 
    response = raises(Response, request_with, None, auther).value
    assert response.code == 401, response

def test_wrong_auth(request_with):
    auth = lambda u, p: u == "username" and p == "password"
    auther = inbound_responder(auth, realm="testrealm@host.com") 
    response = raises(Response, request_with, "Wacky xxx", auther).value
    assert response.code == 400, response


