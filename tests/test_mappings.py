from aspen.http.baseheaders import BaseHeaders
from aspen.http.request import Querystring

def test_headers_are_case_insensitive():
    headers = BaseHeaders('Foo: bar')
    expected = 'bar'
    actual = headers.one('foo')
    assert actual == expected, actual

def test_querystring_basically_works():
    querystring = Querystring('Foo=bar')
    expected = 'bar'
    actual = querystring.one('Foo', default='missing')
    assert actual == expected, actual

def test_querystring_is_case_sensitive():
    querystring = Querystring('Foo=bar')
    expected = 'missing'
    actual = querystring.one('foo', default='missing')
    assert actual == expected, actual

