from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import io

from pytest import raises
from pando.website import Website
from pando.http.response import Response
from pando.exceptions import BadLocation


simple_error_spt = """
[---]
[---] text/plain via stdlib_format
{response.body}
"""


# Tests
# =====

def test_basic():
    website = Website(www_root='pando/www')
    expected = os.path.join(os.getcwd(), 'pando', 'www')
    actual = website.www_root
    assert actual == expected

def test_website_is_accessible_from_first_page_of_simplates(harness):
    harness.fs.www.mk(('index.spt', "website\n[---]\n[---]\n"))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 200, response.body

def test_normal_response_is_returned(harness):
    harness.fs.www.mk(('index.html', "Greetings, program!"))
    expected = b'\r\n'.join(b"""\
HTTP/1.1
Content-Type: text/html

Greetings, program!
""".splitlines())
    actual = harness.client.GET()._to_http('1.1')
    assert actual == expected

def test_fatal_error_response_is_returned(harness):
    harness.fs.www.mk(('index.html.spt', "[---]\nraise heck\n[---]\n"))
    expected = 500
    actual = harness.client.GET(raise_immediately=False).code
    assert actual == expected

def test_dispatch_redirect_works(harness):
    harness.fs.www.mk(('foobar/index.spt', ""))
    r = harness.client.GET('/foobar', raise_immediately=False)
    assert r.code == 302
    assert r.headers[b'Location'] == b'/foobar/'

def test_dispatch_redirect_works_with_unicode(harness):
    harness.fs.www.mk(('%foobar/index.spt', ""))
    r = harness.client.GET('/f%C3%A9e', raise_immediately=False)
    assert r.code == 302
    assert r.headers[b'Location'] == b'/f%C3%A9e/'

def test_redirect_has_only_location(harness):
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
website.redirect('http://elsewhere', code=304)
[---]"""))
    actual = harness.client.GET(raise_immediately=False)
    assert actual.code == 304
    headers = actual.headers
    assert list(headers.keys()) == [b'Location']

def test_nice_error_response_is_returned(harness):
    harness.short_circuit = False
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(500)
[---]"""))
    assert harness.client.GET(raise_immediately=False).code == 500

def test_nice_error_response_is_returned_for_404(harness):
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(404)
[---]"""))
    assert harness.client.GET(raise_immediately=False).code == 404

def test_response_body_doesnt_expose_traceback_by_default(harness):
    harness.fs.project.mk(('error.spt', simple_error_spt))
    harness.fs.www.mk(('index.html.spt', """
[---]
raise Exception("Can I haz traceback ?")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert b"Can I haz traceback ?" not in response.body

def test_response_body_exposes_traceback_for_show_tracebacks(harness):
    harness.fs.project.mk(('error.spt', simple_error_spt))
    harness.fs.www.mk(('index.html.spt', """
[---]
raise Exception("Can I haz traceback ?")
[---]"""))
    harness.client.hydrate_website(show_tracebacks=True)
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert b"Can I haz traceback ?" in response.body

def test_default_error_simplate_doesnt_expose_raised_body_by_default(harness):
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(404, "Um, yeah.")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 404
    assert b"Um, yeah." not in response.body

def test_default_error_simplate_exposes_raised_body_for_show_tracebacks(harness):
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(404, "Um, yeah.")
[---]"""))
    harness.client.hydrate_website(show_tracebacks=True)
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 404
    assert b"Um, yeah." in response.body

def test_nice_error_response_can_come_from_user_error_spt(harness):
    harness.fs.project.mk(('error.spt', '[---]\n[---] text/plain\nTold ya.'))
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(420)
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 420
    assert response.body == b'Told ya.'

def test_nice_error_response_can_come_from_user_420_spt(harness):
    harness.fs.project.mk(('420.spt', """
[---]
msg = "Enhance your calm." if response.code == 420 else "Ok."
[---] text/plain
%(msg)s"""))
    harness.fs.www.mk(('index.html.spt', """
from pando import Response
[---]
raise Response(420)
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 420
    assert response.body == b'Enhance your calm.'

def test_delegate_error_to_simplate_favors_already_negotiated_media_type(harness):
    harness.fs.project.mk(('error.spt', """[---]
[---] text/fake
Lorem ipsum
[---] text/html
<p>Error</p>
[---] text/plain
Error
"""))
    harness.fs.www.mk(('foo.spt',"""
from pando import Response
[---]
raise Response(403)
[---] text/plain
    """))
    response = harness.client.GET('/foo', raise_immediately=False, HTTP_ACCEPT=b'text/fake')
    assert response.code == 403
    # If it hadn't raised an exception `foo.spt` would have returned
    # `text/plain`, so that's what `error.spt` should return.
    assert b'text/plain' in response.headers[b'Content-Type']

def test_delegate_error_to_simplate_falls_back_to_original_accept_header(harness):
    harness.fs.project.mk(('error.spt', """[---]
[---] text/plain
Error
[---] text/fake
Lorem ipsum
"""))
    response = harness.client.GET('/foo', raise_immediately=False, HTTP_ACCEPT=b'text/fake')
    assert response.code == 404
    assert b'text/fake' in response.headers[b'Content-Type']

def test_default_error_spt_handles_text_html(harness):
    harness.fs.www.mk(('foo.html.spt',"""
from pando import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.html', raise_immediately=False)
    assert response.code == 404
    assert b'text/html' in response.headers[b'Content-Type']

def test_default_error_spt_handles_application_json(harness):
    harness.fs.www.mk(('foo.json.spt',"""
from pando import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers[b'Content-Type'] == b'application/json; charset=UTF-8'
    assert response.body == b'''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": ""
 }
'''

def test_default_error_spt_application_json_includes_msg_for_show_tracebacks(harness):
    harness.fs.www.mk(('foo.json.spt',"""
from pando import Response
[---]
raise Response(404, "Right, sooo...")
[---]
    """))
    harness.client.hydrate_website(show_tracebacks=True)
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers[b'Content-Type'] == b'application/json; charset=UTF-8'
    assert response.body == b'''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": "Right, sooo..."
 }
'''

def test_default_error_spt_falls_through_to_text_plain(harness):
    harness.fs.www.mk(('foo.xml.spt',"""
from pando import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers[b'Content-Type'] == b'text/plain; charset=UTF-8'
    assert response.body == b"Not found, program!\n\n"

def test_default_error_spt_fall_through_includes_msg_for_show_tracebacks(harness):
    harness.fs.www.mk(('foo.xml.spt',"""
from pando import Response
[---]
raise Response(404, "Try again!")
[---]
    """))
    harness.client.hydrate_website(show_tracebacks=True)
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers[b'Content-Type'] == b'text/plain; charset=UTF-8'
    assert response.body == b"Not found, program!\nTry again!\n"

def test_custom_error_spt_without_text_plain_doesnt_result_in_406(harness):
    harness.fs.project.mk(('error.spt', """
[---]
[---] text/html
<h1>Oh no!</h1>
    """))
    harness.fs.www.mk(('foo.xml.spt',"""
from pando import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.body == b"<h1>Oh no!</h1>\n"

def test_custom_error_spt_with_text_plain_works(harness):
    harness.fs.project.mk(('error.spt', """
[---]
[---] text/plain
Oh no!
    """))
    harness.fs.www.mk(('foo.xml.spt',"""
from pando import Response
[---]
raise Response(404)
[---]
    """))
    response = harness.client.GET('/foo.xml', raise_immediately=False)
    assert response.code == 404
    assert response.headers[b'Content-Type'] == b'text/plain; charset=UTF-8'
    assert response.body == b"Oh no!\n"


def test_autoindex_response_is_404_by_default(harness):
    harness.fs.www.mk(('README', "Greetings, program!"))
    assert harness.client.GET(raise_immediately=False).code == 404

def test_autoindex_response_is_returned(harness):
    harness.fs.www.mk(('README', "Greetings, program!"))
    harness.client.hydrate_website(list_directories=True)
    body = harness.client.GET(raise_immediately=False).body
    assert b'README' in body

def test_resources_can_import_from_project_root(harness):
    harness.fs.project.mk(('foo.py', 'bar = "baz"'))
    harness.fs.www.mk(('index.html.spt', "from foo import bar\n[---]\n[---]\nGreetings, %(bar)s!"))
    assert harness.client.GET(raise_immediately=False).body == b"Greetings, baz!"

def test_non_500_response_exceptions_dont_get_folded_to_500(harness):
    harness.fs.www.mk(('index.html.spt', '''
from pando import Response
[---]
raise Response(400)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 400

def test_errors_show_tracebacks(harness):
    harness.fs.www.mk(('index.html.spt', '''
from pando import Response
[---]
website.show_tracebacks = 1
raise Response(400,1,2,3,4,5,6,7,8,9)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert b'Response(400,1,2,3,4,5,6,7,8,9)' in response.body


class _TestMiddleware(object):
    """Simple WSGI middleware for testing."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ[b'PATH_INFO'] == '/middleware':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return ['_TestMiddleware']
        return self.app(environ, start_response)

def build_environ(path):
    """Build WSGI environ for testing.

    It's intentional that some keys and values are unicode instead of bytes, we
    need to support both and this is where we test that.
    """
    return {
        b'REQUEST_METHOD': b'GET',
        b'PATH_INFO': path,
         'QUERY_STRING': '',
        b'SERVER_SOFTWARE': b'build_environ/1.0',
        b'SERVER_PROTOCOL': 'HTTP/1.1',
         'wsgi.input': io.BytesIO()
    }

def test_call_wraps_wsgi_middleware(client):
    client.website.state_chain.default_short_circuit = False
    client.website.wsgi_app = _TestMiddleware(client.website.wsgi_app)
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

def test_raised_unicode_response_is_encoded_with_configured_charset(harness):
    harness.fs.www.mk(('index.html.spt', '''
        from pando import Response
        [---]
        raise Response(200, "touch\\u00e9")
        [---]
    '''))
    harness.client.hydrate_website(encode_output_as='latin9')
    def start_response(*a):
        pass
    body = harness.client.website(build_environ('/'), start_response)
    assert list(body) == [b'touch\xe9']


# redirect

def test_redirect_redirects(website):
    assert raises(Response, website.redirect, '/').value.code == 302

def test_redirect_code_is_settable(website):
    assert raises(Response, website.redirect, '/', code=8675309).value.code == 8675309

def test_redirect_permanent_is_301(website):
    assert raises(Response, website.redirect, '/', permanent=True).value.code == 301

def test_redirect_without_website_base_url_is_fine(website):
    assert raises(Response, website.redirect, '/').value.headers[b'Location'] == b'/'

def test_redirect_honors_website_base_url(website):
    website.base_url = 'foo'
    assert raises(Response, website.redirect, '/').value.headers[b'Location'] == b'foo/'

def test_redirect_can_override_base_url_per_call(website):
    website.base_url = 'foo'
    assert raises(Response, website.redirect, '/', base_url='b').value.headers[b'Location'] == b'b/'

def test_redirect_declines_to_construct_bad_urls(website):
    raised = raises(BadLocation, website.redirect, '../foo', base_url='http://www.example.com')
    assert raised.value.body == 'Bad redirect location: http://www.example.com../foo'

def test_redirect_declines_to_construct_more_bad_urls(website):
    raised = raises(BadLocation, website.redirect, 'http://www.example.org/foo',
                                                                 base_url='http://www.example.com')
    expected = 'Bad redirect location: http://www.example.comhttp://www.example.org/foo'
    assert raised.value.body == expected

def test_redirect_will_construct_a_good_absolute_url(website):
    response = raises(Response, website.redirect, '/foo', base_url='http://www.example.com').value
    assert response.headers[b'Location'] == b'http://www.example.com/foo'

def test_redirect_will_allow_a_relative_path(website):
    response = raises(Response, website.redirect, '../foo', base_url='').value
    assert response.headers[b'Location'] == b'../foo'

def test_redirect_will_allow_an_absolute_url(website):
    response = raises(Response, website.redirect, 'http://www.example.org/foo', base_url='').value
    assert response.headers[b'Location'] == b'http://www.example.org/foo'

def test_redirect_can_use_given_response(website):
    response = Response(65, 'Greetings, program!', {b'Location': b'A Town'})
    response = raises(Response, website.redirect, '/flah', response=response).value
    assert response.code == 302                     # gets clobbered
    assert response.headers[b'Location'] == b'/flah'  # gets clobbered
    assert response.body == 'Greetings, program!'   # not clobbered

def test_redirect_doesnt_overescape(website):
    response = raises(Response, website.redirect, '/f%C3%A9e').value
    assert response.headers[b'Location'] == b'/f%C3%A9e'


# canonicalize_base_url

def test_canonicalize_base_url_canonicalizes_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='https://example.com')
    response = harness.client.GxT()
    assert response.code == 302
    assert response.headers[b'Location'] == b'https://example.com/'

def test_canonicalize_base_url_includes_path_and_qs_for_GET(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='https://example.com')
    response = harness.client.GxT('/foo/bar?baz=buz')
    assert response.code == 302
    assert response.headers[b'Location'] == b'https://example.com/foo/bar?baz=buz'

def test_canonicalize_base_url_redirects_to_homepage_for_POST(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='https://example.com')
    response = harness.client.PxST('/foo/bar?baz=buz')
    assert response.code == 302
    assert response.headers[b'Location'] == b'https://example.com/'

def test_canonicalize_base_url_allows_good_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='https://localhost')
    response = harness.client.GET()
    assert response.code == 200
    assert response.body == b'Greetings, program!'

def test_canonicalize_base_url_is_noop_without_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website()
    response = harness.client.GET()
    assert response.code == 200
    assert response.body == b'Greetings, program!'
