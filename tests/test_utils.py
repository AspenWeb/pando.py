from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import aspen.utils # this happens to install the 'repr' error strategy
from aspen.testing import assert_raises, teardown_function
from aspen.utils import ascii_dammit, unicode_dammit, to_age, utcnow
from datetime import datetime

GARBAGE = b"\xef\xf9"


def test_garbage_is_garbage():
    assert_raises(UnicodeDecodeError, lambda s: s.decode('utf8'), GARBAGE)

def test_repr_error_strategy_works():
    errors = 'repr'
    actual = GARBAGE.decode('utf8', errors)
    assert actual == r"\xef\xf9"

def test_unicode_dammit_works():
    actual = unicode_dammit(b"foo\xef\xfar")
    assert actual == r"foo\xef\xfar"

def test_unicode_dammit_fails():
    assert_raises(TypeError, unicode_dammit, 1)
    assert_raises(TypeError, unicode_dammit, [])
    assert_raises(TypeError, unicode_dammit, {})

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
    assert_raises(ValueError, to_age, datetime.utcnow())

def test_to_age_formatting_works():
    actual = to_age(utcnow(), fmt_past="Cheese, for %(age)s!")
    assert actual == "Cheese, for just a moment!"


