# encoding: utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from pando import Response
from pando.exceptions import CRLFInjection
from pando.http.mapping import Mapping, CaseInsensitiveMapping
from pando.http.baseheaders import BaseHeaders


def test_accessing_missing_key_raises_Response():
    m = Mapping()
    raises(Response, lambda k: m[k], 'foo')

def test_mapping_calling_ones_with_missing_key_raises_Response():
    m = Mapping()
    raises(Response, m.ones, 'foo')


def test_case_insensitive_mapping_access_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m['foo'] = 1
    m['fOO'] = 1
    m['FOO'] = 11
    expected = 11
    actual = m['foo']
    assert actual == expected

def test_case_insensitive_mapping_get_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m['foo'] = 11
    m['fOO'] = 1
    m['FOO'] = 1
    expected = 1
    actual = m.get('foo')
    assert actual == expected

def test_case_insensitive_mapping_all_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m.add('foo', 1)
    m.add('fOO', 1)
    m.add('FOO', 1)
    expected = [1, 1, 1, 1]
    actual = m.all('foo')
    assert actual == expected

def test_case_insensitive_mapping_pop_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m['foo'] = 99
    m['fOO'] = 1
    m['FOO'] = 11
    expected = 11
    actual = m.pop('foo')
    assert actual == expected

def test_case_insensitive_mapping_popall_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m.add('foo', 99)
    m.add('fOO', 1)
    m.add('FOO', 11)
    expected = [1, 99, 1, 11]
    actual = m.popall('foo')
    assert actual == expected

def test_case_insensitive_mapping_ones_is_case_insensitive():
    m = CaseInsensitiveMapping()
    m['Foo'] = 1
    m.add('foo', 8)
    m.add('fOO', 9)
    m.add('FOO', 12)
    m['bar'] = 2
    m.add('BAR', 200)
    expected = [12, 200]
    actual = m.ones('Foo', 'Bar')
    assert actual == expected


def test_headers_can_be_raw_when_non_ascii():
    headers = BaseHeaders(b'Foo: b\xc3\xabar\r\nOh: Yeah!')
    assert headers.raw == b'Foo: b\xc3\xabar\r\nOh: Yeah!'

def test_headers_reject_CR_injection():
    with raises(CRLFInjection):
        BaseHeaders(b'')[b'foo'] = b'\rbar'

def test_headers_reject_LF_injection():
    with raises(CRLFInjection):
        BaseHeaders(b'')[b'foo'] = b'\nbar'

def test_headers_reject_CR_injection_from_add():
    with raises(CRLFInjection):
        BaseHeaders(b'').add(b'foo', b'\rbar')

def test_headers_reject_LF_injection_from_add():
    with raises(CRLFInjection):
        BaseHeaders(b'').add(b'foo', b'\nbar')
