# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.resources import decode_raw
from pytest import raises


def test_utf8(harness):
    expected = unichr(1758)
    actual = harness.simple("""
        "#empty first page"
        [------------------]
        text = unichr(1758)
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected

def test_utf8_char(harness):
    expected = u'א'
    actual = harness.simple(b"""
        # encoding=utf8
        "#empty first page"
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected


# decode_raw

def test_decode_raw_can_take_encoding_from_first_line():
    actual = decode_raw(b"""\
    # -*- coding: utf8 -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    text = u'א'
    """
    assert actual == expected

def test_decode_raw_can_take_encoding_from_second_line():
    actual = decode_raw(b"""\
    #!/blah/blah
    # -*- coding: utf8 -*-
    text = u'א'
    """)
    expected = """\
    #!/blah/blah
    # encoding set to utf8
    text = u'א'
    """
    assert actual == expected

def test_decode_raw_prefers_first_line_to_second():
    actual = decode_raw(b"""\
    # -*- coding: utf8 -*-
    # -*- coding: ascii -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    # -*- coding: ascii -*-
    text = u'א'
    """
    assert actual == expected

def test_decode_raw_ignores_third_line():
    actual = decode_raw(b"""\
    # -*- coding: utf8 -*-
    # -*- coding: ascii -*-
    # -*- coding: cornnuts -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    # -*- coding: ascii -*-
    # -*- coding: cornnuts -*-
    text = u'א'
    """
    assert actual == expected

def test_decode_raw_can_take_encoding_from_various_line_formats():
    formats = [ b'-*- coding: utf8 -*-'
              , b'-*- encoding: utf8 -*-'
              , b'coding: utf8'
              , b'  coding: utf8'
              , b'\tencoding: utf8'
              , b'\t flubcoding=utf8'
               ]
    for fmt in formats:
        def test():
            actual = decode_raw(b"""\
            # {0}
            text = u'א'
            """.format(fmt))
            expected = """\
            # encoding set to utf8
            text = u'א'
            """
            assert actual == expected
        yield test

def test_decode_raw_cant_take_encoding_from_bad_line_formats():
    formats = [ b'-*- coding : utf8 -*-'
              , b'foo = 0 -*- encoding: utf8 -*-'
              , b'  coding : utf8'
              , b'encoding : utf8'
              , b'  flubcoding =utf8'
               ]
    for fmt in formats:
        def test():
            raw = b"""\
            # {0}
            text = u'א'
            """.format(fmt)
            raises(UnicodeDecodeError, decode_raw, raw)
        yield test
