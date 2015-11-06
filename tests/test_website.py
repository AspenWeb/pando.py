from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import StringIO

from pytest import raises
from aspen.website import Website
from aspen.http.response import Response
from aspen.exceptions import BadLocation


simple_error_spt = """
[---]
[---] text/plain via stdlib_format
{response.body}
"""


# Tests
# =====

def test_basic():
    website = Website()
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
    harness.fs.www.mk(('index.html.spt', "[---]\nraise heck\n[---]\n"))
    expected = 500
    actual = harness.client.GET(raise_immediately=False).code
    assert actual == expected

def test_redirect_has_only_location(harness):
    harness.fs.www.mk(('index.html.spt', """
from aspen import Response
[---]
website.redirect('http://elsewhere', code=304)
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

def test_response_body_doesnt_expose_traceback_by_default(harness):
    harness.fs.project.mk(('error.spt', simple_error_spt))
    harness.fs.www.mk(('index.html.spt', """
[---]
raise Exception("Can I haz traceback ?")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert "Can I haz traceback ?" not in response.body

def test_response_body_exposes_traceback_for_show_tracebacks(harness):
    harness.client.website.show_tracebacks = True
    harness.fs.project.mk(('error.spt', simple_error_spt))
    harness.fs.www.mk(('index.html.spt', """
[---]
raise Exception("Can I haz traceback ?")
[---]"""))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert "Can I haz traceback ?" in response.body

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
    assert response.body == 'Told ya.'

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
    assert response.body == 'Enhance your calm.'

def test_delegate_error_to_simplate_respects_original_accept_header(harness):
    harness.fs.project.mk(('error.spt', """[---]
[---] text/fake
Lorem ipsum
[---] text/html
<p>Error</p>
[---] text/plain
Error
"""))
    harness.fs.www.mk(('foo.spt',"""
from aspen import Response
[---]
raise Response(404)
[---] text/plain
    """))
    response = harness.client.GET('/foo', raise_immediately=False, HTTP_ACCEPT=b'text/fake')
    assert response.code == 404
    assert 'text/fake' in response.headers['Content-Type']

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
[---]
    """))
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'application/json'
    assert response.body == '''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": ""
 }
'''

def test_default_error_spt_application_json_includes_msg_for_show_tracebacks(harness):
    harness.client.website.show_tracebacks = True
    harness.fs.www.mk(('foo.json.spt',"""
from aspen import Response
[---]
raise Response(404, "Right, sooo...")
[---]
    """))
    response = harness.client.GET('/foo.json', raise_immediately=False)
    assert response.code == 404
    assert response.headers['Content-Type'] == 'application/json'
    assert response.body == '''\
{ "error_code": 404
, "error_message_short": "Not Found"
, "error_message_long": "Right, sooo..."
 }
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
    assert response.body == "Not found, program!\n\n"

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
    assert response.body == "Not found, program!\nTry again!\n"

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
    assert response.body == "Oh no!\n"


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
    harness.fs.www.mk(('index.html.spt', "from foo import bar\n[---]\n[---]\nGreetings, %(bar)s!"))
    assert harness.client.GET(raise_immediately=False).body == "Greetings, baz!"

def test_non_500_response_exceptions_dont_get_folded_to_500(harness):
    harness.fs.www.mk(('index.html.spt', '''
from aspen import Response
[---]
raise Response(400)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 400

def test_errors_show_tracebacks(harness):
    harness.fs.www.mk(('index.html.spt', '''
from aspen import Response
[---]
website.show_tracebacks = 1
raise Response(400,1,2,3,4,5,6,7,8,9)
[---]
'''))
    response = harness.client.GET(raise_immediately=False)
    assert response.code == 500
    assert 'Response(400,1,2,3,4,5,6,7,8,9)' in response.body


# redirect

def test_redirect_redirects(website):
    assert raises(Response, website.redirect, '/').value.code == 302

def test_redirect_code_is_settable(website):
    assert raises(Response, website.redirect, '/', code=8675309).value.code == 8675309

def test_redirect_permanent_is_301(website):
    assert raises(Response, website.redirect, '/', permanent=True).value.code == 301

def test_redirect_without_website_base_url_is_fine(website):
    assert raises(Response, website.redirect, '/').value.headers['Location'] == '/'

def test_redirect_honors_website_base_url(website):
    website.base_url = 'foo'
    assert raises(Response, website.redirect, '/').value.headers['Location'] == 'foo/'

def test_redirect_can_override_base_url_per_call(website):
    website.base_url = 'foo'
    assert raises(Response, website.redirect, '/', base_url='b').value.headers['Location'] == 'b/'

def test_redirect_declines_to_construct_bad_urls(website):
    raised = raises(BadLocation, website.redirect, '../foo', base_url='http://www.example.com')
    assert raised.value.body == 'Bad redirect location: http://www.example.com../foo'

def test_redirect_declines_to_construct_more_bad_urls(website):
    raised = raises(BadLocation, website.redirect, 'http://www.example.org/foo',
                                                                 base_url='http://www.example.com')
    assert raised.value.body == 'Bad redirect location: '\
                                                 'http://www.example.comhttp://www.example.org/foo'

def test_redirect_will_construct_a_good_absolute_url(website):
    response = raises(Response, website.redirect, '/foo', base_url='http://www.example.com').value
    assert response.headers['Location'] == 'http://www.example.com/foo'

def test_redirect_will_allow_a_relative_path(website):
    response = raises(Response, website.redirect, '../foo', base_url='').value
    assert response.headers['Location'] == '../foo'

def test_redirect_will_allow_an_absolute_url(website):
    response = raises(Response, website.redirect, 'http://www.example.org/foo', base_url='').value
    assert response.headers['Location'] == 'http://www.example.org/foo'

def test_redirect_can_use_given_response(website):
    response = Response(65, 'Greetings, program!', {'Location': 'A Town'})
    response = raises(Response, website.redirect, '/flah', response=response).value
    assert response.code == 302                     # gets clobbered
    assert response.headers['Location'] == '/flah'  # gets clobbered
    assert response.body == 'Greetings, program!'   # not clobbered
