# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


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
