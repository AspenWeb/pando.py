from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.http.response import charset_re
from aspen.testing import teardown_function


m = lambda s: charset_re.match(s) is not None


def test_charset_re_works():
    assert m("cheese")

def test_charset_re_disallows_spaces():
    assert not m("cheese head")

def test_charset_re_doesnt_match_empty_string():
    assert not m("")

def test_charset_re_does_match_string_of_one_character():
    assert m("a")

def test_charset_re_does_match_string_of_forty_characters():
    assert m("0123456789012345678901234567890123456789")

def test_charset_re_doesnt_match_string_of_forty_one_characters():
    assert not m("01234567890123456789012345678901234567890")

def test_charset_re_matches_ascii():
    assert m("US-ASCII")

def test_charset_re_matches_utf8():
    assert m("UTF-8")

def test_charset_re_pt():
    assert m("PT")

def test_charset_re_latin1():
    assert m("latin-1")

def test_charset_re_iso88591():
    assert m("ISO-8859-1")

def test_charset_re_windows1252():
    assert m("windows-1252")

def test_charset_re_matches_valid_perl():
    assert m(":_()+.-")
