from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def test_can_use_request_headers(harness):
    response = harness.simple( "foo = request.headers['Foo']\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , HTTP_FOO=b'bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_cookie(harness):
    response = harness.simple( "foo = request.cookie['Foo']\n"
                               "[-----] via stdlib_format\n"
                               "{foo}"
                             , HTTP_COOKIE=b'foo=bar'
                              )
    assert response.body == 'bar'
