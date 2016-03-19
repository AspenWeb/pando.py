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


def test_mapping_subscript_assignment_clobbers():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = ['buz']
    actual = dict.__getitem__(m, 'foo')
    assert actual == expected

def test_mapping_subscript_access_returns_last():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = 'buz'
    actual = m['foo']
    assert actual == expected

def test_mapping_get_returns_last():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = 'buz'
    actual = m.get('foo')
    assert actual == expected

def test_mapping_get_returns_default():
    m = Mapping()
    expected = 'cheese'
    actual = m.get('foo', 'cheese')
    assert actual == expected

def test_mapping_get_default_default_is_None():
    m = Mapping()
    expected = None
    actual = m.get('foo')
    assert actual is expected

def test_mapping_all_returns_list_of_all_values():
    m = Mapping()
    m['foo'] = 'bar'
    m.add('foo', 'baz')
    m.add('foo', 'buz')
    expected = ['bar', 'baz', 'buz']
    actual = m.all('foo')
    assert actual == expected

def test_mapping_ones_returns_list_of_last_values():
    m = Mapping()
    m['foo'] = 1
    m['foo'] = 2
    m['bar'] = 3
    m['bar'] = 4
    m['bar'] = 5
    m['baz'] = 6
    m['baz'] = 7
    m['baz'] = 8
    m['baz'] = 9
    expected = [2, 5, 9]
    actual = m.ones('foo', 'bar', 'baz')
    assert actual == expected

def test_mapping_deleting_a_key_removes_it_entirely():
    m = Mapping()
    m['foo'] = 1
    m['foo'] = 2
    m['foo'] = 3
    del m['foo']
    assert 'foo' not in m

def test_accessing_missing_key_raises_Response():
    m = Mapping()
    raises(Response, lambda k: m[k], 'foo')

def test_mapping_calling_ones_with_missing_key_raises_Response():
    m = Mapping()
    raises(Response, m.ones, 'foo')

def test_mapping_pop_returns_the_last_item():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    expected = 3
    actual = m.pop('foo')
    assert actual == expected

def test_mapping_pop_leaves_the_rest():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    m.pop('foo')
    expected = [1, 1]
    actual = m.all('foo')
    assert actual == expected

def test_mapping_pop_removes_the_item_if_that_was_the_last_value():
    m = Mapping()
    m['foo'] = 1
    m.pop('foo')
    expected = []
    actual = m.keys()
    assert actual == expected

def test_mapping_popall_returns_a_list():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    expected = [1, 1, 3]
    actual = m.popall('foo')
    assert actual == expected

def test_mapping_popall_removes_the_item():
    m = Mapping()
    m['foo'] = 1
    m['foo'] = 1
    m['foo'] = 3
    m.popall('foo')
    assert 'foo' not in m


def test_default_mapping_is_case_insensitive():
    m = Mapping()
    m['Foo'] = 1
    m['foo'] = 1
    m['fOO'] = 1
    m['FOO'] = 1
    expected = [1]
    actual = m.all('foo')
    assert actual == expected

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
    headers = BaseHeaders(b'Foo: bëar\r\nOh: Yeah!')
    assert headers.raw == b'Foo: bëar\r\nOh: Yeah!'

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
