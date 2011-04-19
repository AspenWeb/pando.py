import os
from os.path import join

from aspen._tornado.template import Loader
from aspen.configuration import Configuration
from aspen.http.request import Request
from aspen.tests import DieselReq
from aspen.tests.fsfix import attach_teardown, mk
from aspen.website import Website
from diesel.protocols.http import HttpHeaders, HttpRequest


# Fixture
# =======

def check():
    website = Website(Configuration(['fsfix']))
    website.loader = Loader(join('fsfix', '.aspen'))
    response = website.handle(Request.from_diesel(DieselReq()))
    return response


# Tests
# =====

def test_basic():
    website = Website(Configuration([]))
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
    actual = check()._to_http('1.1')
    assert actual == expected, actual

def test_fatal_error_response_is_returned():
    mk(('index.html', "raise heck"))
    expected = 500
    actual = check().code
    assert actual == expected, actual

def test_nice_error_response_is_returned():
    mk(('index.html', "from aspen import Responseraise Response(500)"))
    expected = 500
    actual = check().code
    assert actual == expected, actual

def test_autoindex_response_is_404_by_default():
    mk(('README', "Greetings, program!"))
    expected = 404
    actual = check().code
    assert actual == expected, actual

def test_autoindex_response_is_returned():
    mk(('.aspen/aspen.conf', '[aspen]\nlist_directories: 1')
       , ('README', "Greetings, program!"))
    expected = True
    actual = 'README' in check().body
    assert actual == expected, actual

def test_simplates_can_import_from_dot_aspen():
    mk( '.aspen'
      , ('.aspen/foo.py', 'bar = "baz"')
      , ('index.html', "import fooGreetings, {{ foo.bar }}!")
       )
    expected = "Greetings, baz!"
    actual = check().body
    assert actual == expected, actual


attach_teardown(globals())
