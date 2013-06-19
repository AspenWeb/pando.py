import os
import StringIO

from aspen.testing import handle, StubRequest
from aspen.testing.fsfix import attach_teardown, FSFIX, mk
from aspen.website import Website


# Tests
# =====

def test_basic():
    website = Website([])
    expected = os.getcwd()
    actual = website.www_root
    assert actual == expected, actual

def test_normal_response_is_returned():
    mk(('index.html', "Greetings, program!"))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Type: text/html

Greetings, program!
""".splitlines())
    actual = handle()._to_http('1.1')
    assert actual == expected, actual

def test_fatal_error_response_is_returned():
    mk(('index.html.spt', "raise heck\n[---]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned():
    mk(('index.html.spt', "from aspen import Response\n[---]\nraise Response(500)\n[---]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned_for_404():
    mk(('index.html.spt', "from aspen import Response\n[---]\nraise Response(404)\n[---]\n"))
    expected = 404
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_404_by_default():
    mk(('README', "Greetings, program!"))
    expected = 404
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_returned():
    mk(('README', "Greetings, program!"))
    body = handle('/', '--list_directories=TrUe').body
    assert 'README' in body, body

def test_resources_can_import_from_dot_aspen():
    mk( '.aspen'
      , ('.aspen/foo.py', 'bar = "baz"')
      , ('index.html.spt', "from foo import bar\n[---]\nGreetings, %(bar)s!")
       )
    expected = "Greetings, baz!"
    project_root = os.path.join(FSFIX, '.aspen')
    actual = handle('/', '--project_root='+project_root).body
    assert actual == expected, actual


def test_double_failure_still_sets_response_dot_request():
    mk( '.aspen'
      , ('.aspen/foo.py', """
def bar(response):
    response.request
""")
      , ( '.aspen/configure-aspen.py'
        , 'import foo\nwebsite.hooks.outbound.append(foo.bar)'
         )
      , ('index.html.spt', "raise heck\n[---]\n")
       )

    # Intentionally break the website object so as to trigger a double failure.
    project_root = os.path.join(FSFIX, '.aspen')
    website = Website(['--www_root='+FSFIX, '--project_root='+project_root])
    del website.renderer_factories

    response = website.handle_safely(StubRequest())

    expected = 500
    actual = response.code
    assert actual == expected, actual


def test_website_doesnt_clobber_outbound():
    mk( ( '.aspen/configure-aspen.py'
        , 'import random\nwebsite.hooks.outbound.append(random.choice)'
         )
       )

    project_root = os.path.join(FSFIX, '.aspen')
    website = Website(['--www_root='+FSFIX, '--project_root='+project_root])

    expected = 2
    actual = len(website.hooks.outbound)
    assert actual == expected, actual


class TestMiddleware(object):
    """Simple WSGI middleware for testing."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/middleware':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return ['TestMiddleware']
        return self.app(environ, start_response)


def build_environ(path):
    """Build WSGI environ for testing."""
    return {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'SERVER_SOFTWARE': 'build_environ/1.0',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.input': StringIO.StringIO()
    }


def test_call_wraps_wsgi_middleware():
    website = Website([])
    website.wsgi_app = TestMiddleware(website.wsgi_app)
    respond = [False, False]
    def start_response_should_404(status, headers):
        assert status.lower().strip() == '404 not found', status
        respond[0] = True
    website(build_environ('/'), start_response_should_404)
    assert respond[0]
    def start_response_should_200(status, headers):
        assert status.lower().strip() == '200 ok', status
        respond[1] = True
    website(build_environ('/middleware'), start_response_should_200)
    assert respond[1]


attach_teardown(globals())
