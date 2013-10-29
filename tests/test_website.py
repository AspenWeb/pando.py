from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import StringIO

from aspen.website import Website


# Tests
# =====

def test_basic():
    website = Website([])
    expected = os.getcwd()
    actual = website.www_root
    assert actual == expected

def test_normal_response_is_returned(mk):
    mk(('index.html', "Greetings, program!"))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Type: text/html

Greetings, program!
""".splitlines())
    actual = handle()._to_http('1.1')
    assert actual == expected

def test_fatal_error_response_is_returned(mk):
    mk(('index.html.spt', "raise heck\n[---]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected

def test_redirect_has_only_location(mk):
    mk(('index.html.spt', "from aspen import Response\n[---]\nrequest.redirect('http://elsewhere', code=304)\n[---]\n"))
    actual = handle()
    assert actual.code == 304
    headers = actual.headers
    assert len(headers) == 1
    assert headers.get('Location') is not None

def test_nice_error_response_is_returned(mk):
    mk(('index.html.spt', "from aspen import Response\n[---]\nraise Response(500)\n[---]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected

def test_nice_error_response_is_returned_for_404(mk):
    mk(('index.html.spt', "from aspen import Response\n[---]\nraise Response(404)\n[---]\n"))
    expected = 404
    actual = handle().code
    assert actual == expected

def test_autoindex_response_is_404_by_default(mk):
    mk(('README', "Greetings, program!"))
    expected = 404
    actual = handle().code
    assert actual == expected

def test_autoindex_response_is_returned(handle):
    mk(('README', "Greetings, program!"))
    body = handle('/', '--list_directories=TrUe').body
    assert 'README' in body

def test_resources_can_import_from_dot_aspen(fs):
    fs.mk( '.aspen'
         , ('.aspen/foo.py', 'bar = "baz"')
         , ('index.html.spt', "from foo import bar\n[---]\nGreetings, %(bar)s!")
          )
    expected = "Greetings, baz!"
    project_root = os.path.join(fs.root, '.aspen')
    actual = handle('/', '--project_root='+project_root).body
    assert actual == expected


def test_double_failure_still_sets_response_dot_request(mk):
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
    assert actual == expected


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
        'REQUEST_METHOD': b'GET',
        'PATH_INFO': path,
        'QUERY_STRING': b'',
        'SERVER_SOFTWARE': b'build_environ/1.0',
        'SERVER_PROTOCOL': b'HTTP/1.1',
        'wsgi.input': StringIO.StringIO()
    }


def test_call_wraps_wsgi_middleware(fs):
    website = Website([])
    website.wsgi_app = TestMiddleware(website.wsgi_app)
    respond = [False, False]
    def start_response_should_404(status, headers):
        assert status.lower().strip() == '404 not found'
        respond[0] = True
    website(build_environ('/'), start_response_should_404)
    assert respond[0]
    def start_response_should_200(status, headers):
        assert status.lower().strip() == '200 ok'
        respond[1] = True
    website(build_environ('/middleware'), start_response_should_200)
    assert respond[1]



