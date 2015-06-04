from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals



def test_default_media_type_works(harness):
    harness.fs.www.mk(('index.spt', """
[---]
[---]
plaintext"""))
    response = harness.client.GET(raise_immediately=False)
    assert "plaintext" in response.body


def test_can_use_request_headers(harness):
    response = harness.simple( "foo = request.headers['Foo']\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , HTTP_FOO=b'bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_cookie(harness):
    response = harness.simple( "foo = request.cookie['foo'].value\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , HTTP_COOKIE=b'foo=bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_path(harness):
    response = harness.simple( "foo = request.path.raw\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                              )
    assert response.body == '/'


def test_can_use_request_qs(harness):
    response = harness.simple( "foo = request.qs['foo']\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'bloo'


def test_can_use_request_method(harness):
    response = harness.simple( "foo = request.method\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'GET'


def test_cant_implicitly_override_state(harness):
    state = harness.simple(
        "resource = 'foo'\n"
        "[---] via stdlib_format\n"
        "{resource}",
        want='state'
    )
    assert state['response'].body == 'foo'
    assert state['resource'] != 'foo'


def test_can_explicitly_override_state(harness):
    response = harness.simple(
        "from aspen import Response\n"
        "state['response'] = Response(299)\n"
        "[---]\n"
        "bar"
    )
    assert response.code == 299
    assert response.body == 'bar'
