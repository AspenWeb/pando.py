from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

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

# tests

def _request_with(authfunc, auth_header):
    request = StubRequest()
    if auth_header is not None:
        request.headers['Authorization'] = auth_header
    hook = inbound_responder(authfunc)
    return hook(request)

def test_good_works():
    request = StubRequest()
    # once to get a WWW-Authenticate header
    hook = inbound_responder(_auth_func("username", "password"), realm="testrealm@host.com")
    response = raises(Response, hook, request).value
    # do something with the header
    auth_headers = _auth_headers(response)
    request.headers['Authorization'] = _digest_auth_for(auth_headers, "username", "password")
    #print repr(request.headers['Authorization'])
    response = hook(request)
    success = request.auth.authorized()
    assert success
    assert request.auth.username() == "username", request.auth.username()

#def test_hard_passwords():
#    for password in [ 'pass', 'username', ':password', ':password:','::::::' ]:
#        request = _request_with(_auth_func("username", "password"), _auth_header("username", "password"))
#        success = request.auth.authorized()
#        assert success
#        assert request.auth.username() == "username", request.auth.username()

def test_no_auth():
    auth = lambda u, p: u == "username" and p == "password"
    response = raises(Response, _request_with, auth, None).value
    assert response.code == 401, response

def test_bad_fails():
    request = StubRequest()
    # once to get a WWW-Authenticate header
    hook = inbound_responder(_auth_func("username", "password"), realm="testrealm@host.com")
    response = raises(Response, hook, request).value
    # do something with the header
    auth_headers = _auth_headers(response)
    request.headers['Authorization'] = _digest_auth_for(auth_headers, "username", "badpassword")
    response = raises(Response, hook, request).value
    assert response.code == 401, response
    assert not request.auth.authorized()

def test_wrong_auth():
    auth = lambda u, p: u == "username" and p == "password"
    response = raises(Response, _request_with, auth, "Wacky xxx").value
    assert response.code == 400, response


