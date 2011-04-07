import os

from aspen.configuration import Configuration
from aspen.http.request import Request
from aspen.tests import DieselReq
from aspen.tests.fsfix import attach_teardown, mk
from aspen.website import Website
from diesel.protocols.http import HttpHeaders, HttpRequest


def test_basic():
    website = Website(Configuration([]))
    expected = os.getcwd()
    actual = website.root
    assert actual == expected, actual

def test_normal_response_is_returned():
    mk(('index.html', "Greetings, program!"))
    website = Website(Configuration(['fsfix']))
    response = website.handle(Request.from_diesel(DieselReq()))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Length: 19
Content-Type: text/html; charset=UTF-8

Greetings, program!
""".splitlines())
    actual = response._to_http('1.1')
    assert actual == expected, actual

def test_fatal_error_response_is_returned():
    mk(('index.html', "raise heck"))
    website = Website(Configuration(['fsfix']))
    response = website.handle(Request.from_diesel(DieselReq()))
    expected = 500
    actual = response.code
    assert actual == expected, actual

def test_nice_error_response_is_returned():
    mk(('index.html', "from aspen import Responseraise Response(500)"))
    website = Website(Configuration(['fsfix']))
    response = website.handle(Request.from_diesel(DieselReq()))
    expected = 500
    actual = response.code
    assert actual == expected, actual

def test_autoindex_response_is_404_by_default():
    mk(('README', "Greetings, program!"))
    website = Website(Configuration(['fsfix']))
    response = website.handle(Request.from_diesel(DieselReq()))
    expected = 404
    actual = response.code
    assert actual == expected, actual

def test_autoindex_response_is_returned():
    mk(('.aspen/aspen.conf', '[aspen]\nautoindex: 1')
       , ('README', "Greetings, program!"))
    website = Website(Configuration(['fsfix']))
    response = website.handle(Request.from_diesel(DieselReq()))
    expected = True
    actual = 'README' in response.body
    assert actual == expected, actual


attach_teardown(globals())
