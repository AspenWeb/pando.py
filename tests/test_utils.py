from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

import aspen.utils # this happens to install the 'repr' error strategy
from aspen.utils import ascii_dammit, unicode_dammit, to_age, to_rfc822, utcnow
from datetime import datetime

GARBAGE = b"\xef\xf9"


def test_garbage_is_garbage():
    raises(UnicodeDecodeError, lambda s: s.decode('utf8'), GARBAGE)

def test_repr_error_strategy_works():
    errors = 'repr'
    actual = GARBAGE.decode('utf8', errors)
    assert actual == r"\xef\xf9"

def test_unicode_dammit_works():
    actual = unicode_dammit(b"foo\xef\xfar")
    assert actual == r"foo\xef\xfar"

def test_unicode_dammit_fails():
    raises(TypeError, unicode_dammit, 1)
    raises(TypeError, unicode_dammit, [])
    raises(TypeError, unicode_dammit, {})

def test_unicode_dammit_decodes_utf8():
    actual = unicode_dammit(b"comet: \xe2\x98\x84")
    assert actual == u"comet: \u2604"

def test_unicode_dammit_takes_encoding():
    actual = unicode_dammit(b"comet: \xe2\x98\x84", encoding="ASCII")
    assert actual == r"comet: \xe2\x98\x84"

def test_ascii_dammit_works():
    actual = ascii_dammit(b"comet: \xe2\x98\x84")
    assert actual == r"comet: \xe2\x98\x84"

def test_to_age_barely_works():
    actual = to_age(utcnow())
    assert actual == "just a moment ago"

def test_to_age_fails():
    raises(ValueError, to_age, datetime.utcnow())

def test_to_age_formatting_works():
    actual = to_age(utcnow(), fmt_past="Cheese, for %(age)s!")
    assert actual == "Cheese, for just a moment!"

def test_to_rfc822():
    expected = 'Thu, 01 Jan 1970 00:00:00 GMT'
    actual = to_rfc822(datetime(1970, 1, 1))
    assert actual == expected


def test_base_url_canonicalizer_canonicalizes_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='http://example.com')
    response = harness.client.GxT()
    assert response.code == 302
    assert response.headers['Location'] == 'http://example.com/'

def test_base_url_canonicalizer_includes_path_and_qs_for_GET(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='http://example.com')
    response = harness.client.GxT('/foo/bar?baz=buz')
    assert response.code == 302
    assert response.headers['Location'] == 'http://example.com/foo/bar?baz=buz'

def test_base_url_canonicalizer_redirects_to_homepage_for_POST(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='http://example.com')
    response = harness.client.PxST('/foo/bar?baz=buz')
    assert response.code == 302
    assert response.headers['Location'] == 'http://example.com/'

def test_base_url_canonicalizer_allows_good_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website(base_url='http://localhost')
    response = harness.client.GET()
    assert response.code == 200
    assert response.body == 'Greetings, program!'

def test_base_url_canonicalizer_is_noop_without_base_url(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    harness.client.hydrate_website()
    response = harness.client.GET()
    assert response.code == 200
    assert response.body == 'Greetings, program!'

def test_base_url_canonicalizer_is_really_noop_without_base_url(harness):
    harness.client.hydrate_website()
    harness.client.website.algorithm['redirect_to_base_url'](harness.client.website, None)

def test_base_url_canonicalizer_is_not_noop_with_base_url(harness):
    harness.client.hydrate_website(base_url='foo')
    with raises(AttributeError):
        harness.client.website.algorithm['redirect_to_base_url'](harness.client.website, None)
