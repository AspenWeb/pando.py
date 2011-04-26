import os
from os.path import join

import diesel.runtime
from aspen._tornado.template import Loader
from aspen.http.request import Request
from aspen.tests import handle, DieselReq
from aspen.tests.fsfix import attach_teardown, mk
from aspen.website import Website
from diesel.protocols.http import HttpHeaders, HttpRequest


# Tests
# =====

def test_basic():
    website = Website([])
    expected = os.getcwd()
    actual = website.root
    assert actual == expected, actual

def test_normal_response_is_returned():
    mk(('index.html', "Greetings, program!"))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Length: 19
Content-Type: text/html; charset=UTF-8

Greetings, program!
""".splitlines())
    actual = handle()._to_http('1.1')
    assert actual == expected, actual

def test_fatal_error_response_is_returned():
    mk(('index.html', "raise heck"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned():
    mk(('index.html', "from aspen import Responseraise Response(500)"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned_for_404():
    mk(('index.html', "from aspen import Responseraise Response(404)"))
    expected = 404 
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_404_by_default():
    mk(('README', "Greetings, program!"))
    expected = 404
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_returned():
    mk(('.aspen/aspen.conf', '[aspen]\nlist_directories: 1')
       , ('README', "Greetings, program!"))
    expected = True
    actual = 'README' in handle().body
    assert actual == expected, actual

def test_simplates_can_import_from_dot_aspen():
    mk( '.aspen'
      , ('.aspen/foo.py', 'bar = "baz"')
      , ('index.html', "import fooGreetings, {{ foo.bar }}!")
       )
    expected = "Greetings, baz!"
    actual = handle().body
    assert actual == expected, actual




def test_double_failure_still_sets_response_dot_request():
    mk( '.aspen'
      , ('.aspen/foo.py', """
def bar(response):
    response.request
""")
      , ('.aspen/hooks.conf', 'foo:bar')
      , ('index.html', "raise heck")
       )

    # Intentionally break the website object so as to trigger a double failure.
    website = Website(['fsfix'])
    del website.template_loader

    response = website.handle(Request.from_diesel(DieselReq()))

    expected = 500
    actual = response.code
    assert actual == expected, actual


attach_teardown(globals())
