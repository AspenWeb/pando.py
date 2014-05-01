# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.resources import decode_raw
from aspen.exceptions import LoadError
from pytest import raises


def test_non_ascii_bytes_fail_without_encoding(harness):
    raises(LoadError, harness.simple, b"""
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """)

def test_non_ascii_bytes_work_with_encoding(harness):
    expected = u'א'
    actual = harness.simple(b"""
        # encoding=utf8
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected

def test_response_as_wsgi_does_something_sane(harness):
    expected = u'א'.encode('utf8')
    wsgi = harness.simple(b"""
        # encoding=utf8
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """)

    actual = ''.join(list(wsgi({}, lambda a,b: None)))
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
