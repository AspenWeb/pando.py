from aspen.http.headers import Headers
from aspen.http.wwwform import WwwForm

def test_headers_are_case_insensitive():
    headers = Headers('Foo: bar')
    expected = 'bar'
    actual = headers.one('foo')
    assert actual == expected, actual

def test_wwwform_is_case_sensitive():
    wwwform = WwwForm('Foo: bar')
    expected = 'missing'
    actual = wwwform.one('foo', default='missing')
    assert actual == expected, actual

