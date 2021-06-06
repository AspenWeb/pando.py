from pando.http.request import Request
from pando.http.response import Response


def test_website_can_respond(harness):
    harness.fs.www.mk(('index.html.spt', '[---]\n[---]\nGreetings, program!'))
    assert harness.client.GET().body == b'Greetings, program!'


def test_website_can_respond_with_negotiation(harness):
    harness.fs.www.mk(('index.spt', '''
        [---]
        [---] text/plain
        Greetings, program!
        [---] text/html
        <h1>Hi!
    '''))
    assert harness.client.GET(HTTP_ACCEPT=b'text/html').body == b'<h1>Hi!\n'


def test_404_comes_out_404(harness):
    harness.fs.project.mk(('404.spt', '[---]\n[---] text/plain\nEep!'))
    assert harness.client.GET(raise_immediately=False).code == 404


def test_user_can_influence_request_context_via_chain_state(harness):
    harness.fs.www.mk(('index.html.spt', '[---]\n[---]\n%(foo)s'))

    def add_foo_to_context(request):
        return {'foo': 'bar'}

    harness.client.website.state_chain.insert_after(
        'parse_environ_into_request', add_foo_to_context
    )
    assert harness.client.GET().body == b'bar'


def test_simplates_dont_implicitly_override_state(harness):
    harness.fs.www.mk(('index.spt', """
        [---]
        resource = 'foo'
        [---] via stdlib_format
        {resource}
    """))
    state = harness.client.GET('/', want='state')
    assert state['response'].body == b'foo\n'
    assert state['resource'] != 'foo'


def test_simplates_can_explicitly_override_state(harness):
    harness.fs.www.mk(('index.spt', """\
        [---]
        state['resource'] = 'foo'
        [---]
    """))
    state = harness.client.GET("/", want='state')
    assert state['resource'] == 'foo'


def test_simplates_can_modify_output(harness):
    harness.fs.www.mk(('index.spt', """\
        [---]
        output.body = 'thé'
        output.media_type = 'text/x-foobar'
        output.charset = 'utf16'
        [---]
    """))
    response = harness.client.GET("/")
    assert response.body == 'thé'.encode('utf16')
    assert response.headers[b'Content-Type'] == b'text/x-foobar; charset=utf16'


def test_early_failures_dont_break_everything(harness):
    old_from_wsgi = Request.from_wsgi

    def broken_from_wsgi(*a, **kw):
        raise Response(400)

    try:
        Request.from_wsgi = classmethod(broken_from_wsgi)
        assert harness.client.GET("/", raise_immediately=False).code == 400
    finally:
        Request.from_wsgi = old_from_wsgi


def test_static_resource_GET(harness):
    harness.fs.www.mk(('file.js', "Hello world!"))
    r = harness.client.GET('/file.js')
    assert r.code == 200
    assert r.body == b"Hello world!"


def test_static_resource_HEAD(harness):
    harness.fs.www.mk(('file.js', "Hello world!"))
    r = harness.client.HEAD('/file.js')
    assert r.code == 200
    assert not r.body
    assert r.headers[b'Content-Length'] == b'12'


def test_static_resource_PUT(harness):
    harness.fs.www.mk(('file.js', "Hello world!"))
    r = harness.client.xPUT('/file.js', body=b'Malicious JS code.')
    assert r.code == 405


def test_static_resource_unknown_method(harness):
    harness.fs.www.mk(('file.js', "Hello world!"))
    r = harness.client.hxt('UNKNOWN', '/file.js')
    assert r.code == 405


def test_raise_200_for_OPTIONS(harness):
    r = harness.client.hxt('OPTIONS', '*')
    assert r.code == 204
    assert not r.body
