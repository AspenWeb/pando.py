# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pando.exceptions import LoadError
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
        %(text)s""")
    actual = b''.join(list(wsgi({}, lambda a,b: None)))
    assert actual == expected

def test_the_exec_machinery_handles_two_encoding_lines_properly(harness):
    expected = u'א'
    actual = harness.simple(b"""\
        # encoding=utf8
        # encoding=ascii
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected
