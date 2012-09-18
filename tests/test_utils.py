import aspen.utils # this happens to install the 'repr' error strategy
from aspen.testing import assert_raises, attach_teardown
from aspen.utils import ascii_dammit, unicode_dammit, to_age, utcnow

GARBAGE = "\xef\xf9"


def test_garbage_is_garbage():
    assert_raises(UnicodeDecodeError, lambda s: s.decode('utf8'), GARBAGE)

def test_repr_error_strategy_works():
    errors = 'repr'
    actual = "\xef\xf9".decode('utf8', errors)
    assert actual == r"\xef\xf9", actual

def test_unicode_dammit_works():
    actual = unicode_dammit("foo\xef\xfar")
    assert actual == r"foo\xef\xfar", actual

def test_unicode_dammit_decodes_utf8():
    actual = unicode_dammit("comet: \xe2\x98\x84")
    assert actual == u"comet: \u2604", actual

def test_unicode_dammit_takes_encoding():
    actual = unicode_dammit("comet: \xe2\x98\x84", encoding="ASCII")
    assert actual == r"comet: \xe2\x98\x84", actual

def test_ascii_dammit_works():
    actual = ascii_dammit("comet: \xe2\x98\x84")
    assert actual == r"comet: \xe2\x98\x84", actual

def test_to_age_barely_works():
    actual = to_age(utcnow())
    assert actual == "just a moment ago", actual

def test_to_age_formatting_works():
    actual = to_age(utcnow(), fmt_past="Cheese, for %(age)s!")
    assert actual == "Cheese, for just a moment!", actual


attach_teardown(globals())
