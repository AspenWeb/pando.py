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

SIMPLATE="""
[---]
foo = %s
[---] via stdlib_format
{foo}"""

def test_can_use_request_headers(harness):
    response = harness.simple( SIMPLATE % "request.headers['Foo']"
                             , HTTP_FOO=b'bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_cookie(harness):
    response = harness.simple( SIMPLATE % "request.cookie['foo'].value"
                             , HTTP_COOKIE=b'foo=bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_path(harness):
    response = harness.simple( SIMPLATE % "request.path.raw"
                              )
    assert response.body == '/'


def test_can_use_request_qs(harness):
    response = harness.simple( SIMPLATE % "request.qs['foo']"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'bloo'


def test_can_use_request_method(harness):
    response = harness.simple( SIMPLATE % "request.method"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'GET'


def test_cant_implicitly_override_state(harness):
    state = harness.simple("[---]\n"
        "resource = 'foo'\n"
        "[---] via stdlib_format\n"
        "{resource}",
        want='state'
    )
    assert state['response'].body == 'foo'
    assert state['resource'] != 'foo'


def test_can_explicitly_override_state(harness):
    response = harness.simple("[---]\n"
        "from aspen import Response\n"
        "state['response'] = Response(299)\n"
        "[---]\n"
        "bar"
    )
    assert response.code == 299
    assert response.body == 'bar'


def test_but_python_sections_exhibit_module_scoping_behavior(harness):
    response = harness.simple("""[---]
bar = 'baz'
def foo():
    return bar
foo = foo()
[---] text/html via stdlib_format
{foo}""")
    assert response.body == 'baz'
