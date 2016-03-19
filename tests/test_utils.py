from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

import pando.utils # this happens to install the 'repr' error strategy
from pando.utils import ascii_dammit, unicode_dammit, to_age, to_rfc822, utcnow
from datetime import datetime, timedelta

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
    now = utcnow()
    actual = to_age(now, dt_now=now)
    assert actual == "in just a moment"

    wait = timedelta(seconds=0.5)
    actual = to_age(now - wait, dt_now=now)
    assert actual == "just a moment ago"

def test_to_age_fails():
    raises(ValueError, to_age, datetime.utcnow())

def test_to_age_formatting_works():
    now = utcnow()
    actual = to_age(now, fmt_future="Cheese, for %(age)s!", dt_now=now)
    assert actual == "Cheese, for just a moment!"

def test_to_rfc822():
    expected = 'Thu, 01 Jan 1970 00:00:00 GMT'
    actual = to_rfc822(datetime(1970, 1, 1))
    assert actual == expected
