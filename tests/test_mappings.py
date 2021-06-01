from pytest import raises

from pando import Response
from pando.exceptions import CRLFInjection
from pando.http.mapping import Mapping, CaseInsensitiveMapping, BytesMapping
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


def test_bytes_mapping():
    m = BytesMapping()
    keys = (b'foo', 'foo', 'à'.encode('utf8'), 'à', 0)
    for k in keys:
        for v in keys:
            m[k] = v
            m.add(k, v)
            assert k in m
            if isinstance(k, str):
                expected = v.decode('utf8') if isinstance(v, bytes) else v
                assert m[k] == expected
                assert m.get(k) == expected
                assert m.all(k) == [expected, expected]
                assert m.pop(k) == expected
                assert m.popall(k) == [expected]
            else:
                expected = v.encode('utf8') if isinstance(v, str) else v
                assert m[k] == expected
                assert m.get(k) == expected
                assert m.all(k) == [expected, expected]
                assert m.pop(k) == expected
                assert m.popall(k) == [expected]


def test_headers_can_be_raw_when_non_ascii():
    headers = BaseHeaders({b'Foo': b'b\xc3\xabar', b'Oh': b'Yeah!'})
    assert headers.raw == b'Foo: b\xc3\xabar\r\nOh: Yeah!'

def test_headers_reject_CR_injection():
    with raises(CRLFInjection):
        BaseHeaders()[b'foo'] = b'\rbar'

def test_headers_reject_LF_injection():
    with raises(CRLFInjection):
        BaseHeaders()[b'foo'] = b'\nbar'

def test_headers_reject_CR_injection_from_add():
    with raises(CRLFInjection):
        BaseHeaders().add(b'foo', b'\rbar')

def test_headers_reject_LF_injection_from_add():
    with raises(CRLFInjection):
        BaseHeaders().add(b'foo', b'\nbar')
