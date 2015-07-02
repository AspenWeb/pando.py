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


def test_python_sections_exhibit_module_scoping_behavior(harness):
    response = harness.simple("""
bar = 'baz'
def foo():
    return bar
foo = foo()
[---] text/html via stdlib_format
{foo}""")
    assert response.body == 'baz'


def test_can_influence_render_context_from_algorithm_functions(harness):

    from aspen.renderers import stdlib_format as base


    # Approximate Jinja2's support for calling functions inside a template.

    class CallingStdlibFormat(base.Renderer):
        def render_content(self, context):
            context['_'] = context['_']()
            return base.Renderer.render_content(self, context)

    class CallingStdlibFormatFactory(base.Factory):
        Renderer = CallingStdlibFormat


    # Approximate Gratipay's i18n wiring.

    class HTMLRenderer(CallingStdlibFormat):
        def render_content(self, context):
            context['escape'] = lambda s: 'bar'
            return CallingStdlibFormat.render_content(self, context)

    class Factory(CallingStdlibFormatFactory):
        Renderer = HTMLRenderer

    def get_text(s, state):
        return state['escape'](s)

    def setup(state):
        state['escape'] = lambda s: s
        state['_'] = lambda: get_text('foo', state)

    harness.client.website.renderer_factories['htmlescaped'] = Factory(harness.client.website)
    harness.client.website.algorithm.insert_before('dispatch_request_to_filesystem', setup)
    response = harness.simple("""\
foo = _()
[---] text/html via htmlescaped
{foo}{_}""")
    assert response.body == 'foobar'
