from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

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

def test_resources_can_import_from_project_root(harness):
    harness.fs.project.mk(('foo.py', 'bar = "baz"'))
    harness.fs.www.mk(('index.html.spt', "from foo import bar\n[---]\n[---]\nGreetings, %(bar)s!"))
    assert harness.client.GET(raise_immediately=False).body == "Greetings, baz!"


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
