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

def test_normal_response_is_returned(harness):
    harness.fs.www.mk(('index.html', "Greetings, program!"))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Type: text/html

Greetings, program!
""".splitlines())
    actual = harness.client.GET()._to_http('1.1')
    assert actual == expected

def test_fatal_error_response_is_returned(harness):
    harness.fs.www.mk(('index.html.spt', "raise heck\n[---]\n"))
    expected = 500
    actual = harness.client.GET(raise_immediately=False).code
    assert actual == expected

def test_redirect_has_only_location(harness):
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
request.redirect('http://elsewhere', code=304)
[---]"""))
    actual = harness.client.GET(raise_immediately=False)
    assert actual.code == 304
    headers = actual.headers
    assert headers.keys() == ['Location']

def test_nice_error_response_is_returned(harness):
    harness.short_circuit = False
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(500)
[---]"""))
    assert harness.client.GET(raise_immediately=False).code == 500

def test_nice_error_response_is_returned_for_404(harness):
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(404)
[---]"""))
    assert harness.client.GET(raise_immediately=False).code == 404

def test_default_error_simplate_doesnt_expose_raised_body_by_default(harness):
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(404, "Um, yeah.")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 404
    assert "Um, yeah." not in response.body

def test_default_error_simplate_exposes_raised_body_for_show_tracebacks(harness):
    harness.client.website.show_tracebacks = True
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(404, "Um, yeah.")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 404
    assert "Um, yeah." in response.body

def test_nice_error_response_can_come_from_user_error_spt(harness):
    harness.fs.project.mk(('error.spt', '[---]\n[---] text/plain\nTold ya.'))
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(420)
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 420
    assert response.body.strip() == 'Told ya.'

def test_nice_error_response_can_come_from_user_420_spt(harness):
    harness.fs.project.mk(('420.spt', """
[---]
msg = "Enhance your calm." if response.code == 420 else "Ok."
[---] text/plain
%(msg)s"""))
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
raise Response(420)
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 420
    assert response.body.strip() == 'Enhance your calm.'

def test_default_error_spt_handles_text_html(harness):
    harness.fs.www.mk(('foo.html.spt',"""
from aspen import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.html', raise_immediately=False)
    assert response.code == 404
    assert 'text/html' in response.headers['Content-Type']

def test_default_error_spt_handles_application_json(harness):
    harness.fs.www.mk(('foo.json.spt',"""
from aspen import Response
[---]
raise Response(404)
    """))
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'application/json'
    assert response.body.strip() == '''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": ""
 }\
'''

def test_default_error_spt_application_json_includes_msg_for_show_tracebacks(harness):
    harness.client.website.show_tracebacks = True
    harness.fs.www.mk(('foo.json.spt',"""
from aspen import Response
[---]
raise Response(404, "Right, sooo...")
    """))
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'application/json'
    assert response.body.strip() == '''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": "Right, sooo..."
 }\
'''

def test_default_error_spt_falls_through_to_text_plain(harness):
    harness.fs.www.mk(('foo.xml.spt',"""
from aspen import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'text/plain; charset=UTF-8'
    assert response.body.strip() == "Not found, program!"

def test_default_error_spt_fall_through_includes_msg_for_show_tracebacks(harness):
    harness.client.website.show_tracebacks = True
    harness.fs.www.mk(('foo.xml.spt',"""
from aspen import Response
[---]
raise Response(404, "Try again!")
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'text/plain; charset=UTF-8'
    assert response.body.strip() == "Not found, program!\nTry again!"

def test_custom_error_spt_without_text_plain_results_in_406(harness):
    harness.fs.project.mk(('error.spt', """
[---]
[---] text/html
<h1>Oh no!</h1>
    """))
    harness.fs.www.mk(('foo.xml.spt',"""
from aspen import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 406

def test_custom_error_spt_with_text_plain_works(harness):
    harness.fs.project.mk(('error.spt', """
[---]
[---] text/plain
Oh no!
    """))
    harness.fs.www.mk(('foo.xml.spt',"""
from aspen import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'text/plain; charset=UTF-8'
    assert response.body.strip() == "Oh no!"


def test_autoindex_response_is_404_by_default(harness):
    harness.fs.www.mk(('README', "Greetings, program!"))
    assert harness.client.GET(raise_immediately=False).code == 404

def test_autoindex_response_is_returned(harness):
    harness.fs.www.mk(('README', "Greetings, program!"))
    harness.client.website.list_directories = True
    body = harness.client.GET(raise_immediately=False).body
    assert 'README' in body

def test_resources_can_import_from_project_root(harness):
    harness.fs.project.mk(('foo.py', 'bar = "baz"'))
    harness.fs.www.mk(('index.html.spt', "from foo import bar\n[---]\nGreetings, %(bar)s!"))
    assert harness.client.GET(raise_immediately=False).body == "\n\nGreetings, baz!"

def test_non_500_response_exceptions_dont_get_folded_to_500(harness):
    harness.fs.www.mk(('index.html.spt', '''
from aspen import Response
raise Response(400)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 400

def test_errors_show_tracebacks(harness):
    harness.fs.www.mk(('index.html.spt', '''
from aspen import Response
website.show_tracebacks = 1
raise Response(400,1,2,3,4,5,6,7,8,9)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert 'Response(400,1,2,3,4,5,6,7,8,9)' in response.body


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

def test_call_wraps_wsgi_middleware(client):
    client.website.algorithm.default_short_circuit = False
    client.website.wsgi_app = TestMiddleware(client.website.wsgi_app)
    respond = [False, False]
    def start_response_should_404(status, headers):
        assert status.lower().strip() == '404 not found'
        respond[0] = True
    client.website(build_environ('/'), start_response_should_404)
    assert respond[0]
    def start_response_should_200(status, headers):
        assert status.lower().strip() == '200 ok'
        respond[1] = True
    client.website(build_environ('/middleware'), start_response_should_200)
    assert respond[1]
