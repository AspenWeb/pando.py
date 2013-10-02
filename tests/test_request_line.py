from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from aspen import Response
from aspen.http.request import Request
from aspen.http.mapping import Mapping
from aspen.http.request import Line, Method, URI, Version, Path, Querystring
from aspen.testing import teardown_function


# Line
# ====

def test_line_works():
    line = Line("GET", "/", "HTTP/0.9")
    assert line == u"GET / HTTP/0.9"

def test_line_has_method():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.method == u"GET"

def test_line_has_uri():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.uri == u"/"

def test_line_has_version():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.version == u"HTTP/0.9"

def test_line_chokes_on_non_ASCII_in_uri():
    raises(UnicodeDecodeError, Line, "GET", chr(128), "HTTP/1.1")


# Method
# ======

def test_method_works():
    method = Method("GET")
    assert method == u"GET"

def test_method_is_unicode_subclass():
    method = Method("GET")
    assert issubclass(method.__class__, unicode)

def test_method_is_unicode_instance():
    method = Method("GET")
    assert isinstance(method, unicode)

def test_method_is_basestring_instance():
    method = Method("GET")
    assert isinstance(method, basestring)

def test_method_raw_works():
    method = Method("GET")
    assert method.raw == "GET"

def test_method_raw_is_bytestring():
    method = Method(b"GET")
    assert isinstance(method.raw, str)

def test_method_cant_have_more_attributes():
    method = Method("GET")
    raises(AttributeError, setattr, method, "foo", "bar")

def test_method_can_be_OPTIONS(): assert Method("OPTIONS") == u"OPTIONS"
def test_method_can_be_GET():     assert Method("GET")     == u"GET"
def test_method_can_be_HEAD():    assert Method("HEAD")    == u"HEAD"
def test_method_can_be_POST():    assert Method("POST")    == u"POST"
def test_method_can_be_PUT():     assert Method("PUT")     == u"PUT"
def test_method_can_be_DELETE():  assert Method("DELETE")  == u"DELETE"
def test_method_can_be_TRACE():   assert Method("TRACE")   == u"TRACE"
def test_method_can_be_CONNECT(): assert Method("CONNECT") == u"CONNECT"

def test_method_can_be_big():
    big = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--"
    assert Method(big) == big

def test_method_we_cap_it_at_64_bytes_just_cause____I_mean___come_on___right():
    big = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--!"
    assert raises(Response, Method, big).value.code == 501

def test_method_cant_be_non_ASCII():
    assert raises(Response, Method, b"\x80").value.code == 501

def test_method_can_be_valid_perl():
    assert Method("!#$%&'*+-.^_`|~") == u"!#$%&'*+-.^_`|~"

def the501(i):
    assert raises(Response, Method, chr(i)).value.code == 501

# 0-31
def test_method_no_chr_0(): the501(0)
def test_method_no_chr_1(): the501(1)
def test_method_no_chr_2(): the501(2)
def test_method_no_chr_3(): the501(3)
def test_method_no_chr_4(): the501(4)
def test_method_no_chr_5(): the501(5)
def test_method_no_chr_6(): the501(6)
def test_method_no_chr_7(): the501(7)
def test_method_no_chr_8(): the501(8)
def test_method_no_chr_9(): the501(9)

def test_method_no_chr_10(): the501(10)
def test_method_no_chr_11(): the501(11)
def test_method_no_chr_12(): the501(12)
def test_method_no_chr_13(): the501(13)
def test_method_no_chr_14(): the501(14)
def test_method_no_chr_15(): the501(15)
def test_method_no_chr_16(): the501(16)
def test_method_no_chr_17(): the501(17)
def test_method_no_chr_18(): the501(18)
def test_method_no_chr_19(): the501(19)

def test_method_no_chr_20(): the501(20)
def test_method_no_chr_21(): the501(21)
def test_method_no_chr_22(): the501(22)
def test_method_no_chr_23(): the501(23)
def test_method_no_chr_24(): the501(24)
def test_method_no_chr_25(): the501(25)
def test_method_no_chr_26(): the501(26)
def test_method_no_chr_27(): the501(27)
def test_method_no_chr_28(): the501(28)
def test_method_no_chr_29(): the501(29)

def test_method_no_chr_30(): the501(30)
def test_method_no_chr_31(): the501(31)
def test_method_no_chr_32(): the501(32) # space
def test_method_no_chr_33(): assert Method(chr(33)) == '!'

# SEPARATORS
def test_method_no_chr_40(): the501(40) # (
def test_method_no_chr_41(): the501(41) # )
def test_method_no_chr_60(): the501(60) # <
def test_method_no_chr_62(): the501(62) # >
def test_method_no_chr_64(): the501(64) # @
def test_method_no_chr_44(): the501(44) # ,
def test_method_no_chr_59(): the501(59) # ;
def test_method_no_chr_58(): the501(58) # :
def test_method_no_chr_92(): the501(92) # \
def test_method_no_chr_34(): the501(34) # "
def test_method_no_chr_47(): the501(47) # /
def test_method_no_chr_91(): the501(91) # [
def test_method_no_chr_93(): the501(93) # ]
def test_method_no_chr_63(): the501(63) # ?
def test_method_no_chr_61(): the501(61) # =
def test_method_no_chr_123(): the501(123) # {
def test_method_no_chr_125(): the501(125) # }
def test_method_no_chr_32(): the501(32) # SP
def test_method_no_chr_9(): the501(9) # HT


# URI
# ===

def test_uri_works_at_all():
    uri = URI("/")
    expected = u"/"
    actual = uri
    assert actual == expected

def test_a_nice_unicode_uri():
    uri = URI(b"http://%E2%98%84:bar@localhost:5370/+%E2%98%84.html?%E2%98%84=%E2%98%84+bar")
    assert uri == "http://%E2%98%84:bar@localhost:5370/+%E2%98%84.html?%E2%98%84=%E2%98%84+bar", uri


def test_uri_sets_scheme():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.scheme == u"http", uri.scheme

def test_uri_sets_username():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.username == u"foobar", uri.username

def test_uri_sets_password():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.password == u"secret", uri.password

def test_uri_sets_host():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.host == u"www.example.com", uri.host

def test_uri_sets_port():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.port == 8080, uri.port

def test_uri_sets_path():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.path.decoded == u"/baz.html", uri.path.decoded

def test_uri_sets_querystring():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.querystring.decoded == u"buz=bloo", uri.querystring.decoded


def test_uri_scheme_is_unicode():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.scheme, unicode)

def test_uri_username_is_unicode():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.username, unicode)

def test_uri_password_is_unicode():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.password, unicode)

def test_uri_host_is_unicode():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.host, unicode)

def test_uri_port_is_int():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.port, int)

def test_uri_path_is_Mapping():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.path, Mapping)

def test_uri_querystring_is_Mapping():
    uri = URI("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(uri.querystring, Mapping)


def test_uri_empty_scheme_is_empty_unicode():
    uri = URI("://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.scheme == u"", uri.scheme
    assert isinstance(uri.scheme, unicode), uri.scheme.__class__

def test_uri_empty_username_is_empty_unicode():
    uri = URI("http://:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.username == u"", uri.username
    assert isinstance(uri.username, unicode), uri.username.__class__

def test_uri_empty_password_is_empty_unicode():
    uri = URI("http://foobar:@www.example.com:8080/baz.html?buz=bloo")
    assert uri.password == u"", uri.password
    assert isinstance(uri.password, unicode), uri.password.__class__

def test_uri_empty_host_is_empty_unicode():
    uri = URI("http://foobar:secret@:8080/baz.html?buz=bloo")
    assert uri.host == u"", uri.host
    assert isinstance(uri.host, unicode), uri.host.__class__

def test_uri_empty_port_is_0():
    uri = URI("://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert uri.port == 0, uri.port


def test_uri_normal_case_is_normal():
    uri = URI("/baz.html?buz=bloo")
    assert uri.path == Path("/baz.html")
    assert uri.querystring == Querystring("buz=bloo")


def test_uri_ASCII_worketh():
    uri = URI(chr(127))
    assert uri == unichr(127), uri

def test_uri_non_ASCII_worketh_not():
    raises(UnicodeDecodeError, URI, chr(128))

def test_uri_encoded_username_is_unencoded_properly():
    uri = URI(b"http://%e2%98%84:secret@www.example.com/foo.html")
    assert uri.username == u'\u2604', uri.username

def test_uri_encoded_password_is_unencoded_properly():
    uri = URI(b"http://foobar:%e2%98%84@www.example.com/foo.html")
    assert uri.password == u'\u2604', uri.password

def test_uri_international_domain_name_comes_out_properly():
    uri = URI("http://www.xn--cev.tk/foo.html")
    assert uri.host == u'www.\u658b.tk', uri.host

def test_uri_bad_international_domain_name_raises_UnicodeError():
    raises(UnicodeError, URI, "http://www.xn--ced.tk/foo.html")

def test_uri_raw_is_available_on_something():
    uri = URI("http://www.xn--cev.tk/")
    assert uri.host.raw == "www.xn--cev.tk", uri.host.raw



# Version
# =======

def test_version_can_be_HTTP_0_9():
    actual = Version("HTTP/0.9")
    expected = u"HTTP/0.9"
    assert actual == expected

def test_version_can_be_HTTP_1_0():
    actual = Version("HTTP/1.0")
    expected = u"HTTP/1.0"
    assert actual == expected

def test_version_can_be_HTTP_1_1():
    actual = Version("HTTP/1.1")
    expected = u"HTTP/1.1"
    assert actual == expected

def test_version_cant_be_HTTP_1_2():
    assert raises(Response, Version, b"HTTP/1.2").value.code == 505

def test_version_cant_be_junk():
    assert raises(Response, Version, b"http flah flah").value.code == 400

def test_version_cant_even_be_lowercase():
    assert raises(Response, Version, b"http/1.1").value.code == 400

def test_version_cant_even_be_lowercase():
    assert raises(Response, Version, b"http/1.1").value.code == 400

def test_version_with_garbage_is_safe():
    r = raises(Response, Version, b"HTTP\xef/1.1").value
    assert r.code == 400, r.code
    assert r.body == "Bad HTTP version: HTTP\\xef/1.1.", r.body

def test_version_major_is_int():
    version = Version("HTTP/1.0")
    expected = 1
    actual = version.major
    assert actual == expected

def test_version_major_is_int():
    version = Version("HTTP/0.9")
    expected = 9
    actual = version.minor
    assert actual == expected

def test_version_info_is_tuple():
    version = Version("HTTP/0.9")
    expected = (0, 9)
    actual = version.info
    assert actual == expected

def test_version_raw_is_bytestring():
    version = Version(b"HTTP/0.9")
    expected = str
    actual = version.raw.__class__
    assert actual is expected


# Path
# ====

def test_path_starts_empty():
    path = Path("/bar.html")
    assert path == {}, path

def test_path_has_raw_set():
    path = Path("/bar.html")
    assert path.raw == "/bar.html", path.raw

def test_path_raw_is_str():
    path = Path(b"/bar.html")
    assert isinstance(path.raw, str)

def test_path_has_decoded_set():
    path = Path("/bar.html")
    assert path.decoded == u"/bar.html", path.decoded

def test_path_decoded_is_unicode():
    path = Path("/bar.html")
    assert isinstance(path.decoded, unicode)

def test_path_unquotes_and_decodes_UTF_8():
    path = Path(b"/%e2%98%84.html")
    assert path.decoded == u"/\u2604.html", path.decoded

def test_path_doesnt_unquote_plus():
    path = Path("/+%2B.html")
    assert path.decoded == u"/++.html", path.decoded

def test_path_has_parts():
    path = Path("/foo/bar.html")
    assert path.parts == ['foo', 'bar.html']


# Path params
# ===========

def _extract_params(uri):
#    return dispatcher.extract_rfc2396_params(path.lstrip('/').split('/'))
    params = [ segment.params for segment in uri.path.parts ]
    segments = [ unicode(segment) for segment in uri.path.parts ]
    return ( segments, params )

def test_extract_path_params_with_none():
    request = Request(uri="/foo/bar")
    actual = _extract_params(request.line.uri)
    expected = (['foo', 'bar'], [{}, {}])
    assert actual == expected

def test_extract_path_params_simple():
    request = Request(uri="/foo;a=1;b=2;c/bar;a=2;b=1")
    actual = _extract_params(request.line.uri)
    expected = (['foo', 'bar'], [{'a':['1'], 'b':['2'], 'c':['']}, {'a':['2'], 'b':['1']}])
    assert actual == expected

def test_extract_path_params_complex():
    request = Request(uri="/foo;a=1;b=2,3;c;a=2;b=4/bar;a=2,ab;b=1")
    actual = _extract_params(request.line.uri)
    expected = (['foo', 'bar'], [{'a':['1','2'], 'b':['2,3', '4'], 'c':['']}, {'a':[ '2,ab' ], 'b':['1']}])
    assert actual == expected

def test_path_params_api():
    request = Request(uri="/foo;a=1;b=2;b=3;c/bar;a=2,ab;b=1")
    parts, params = (['foo', 'bar'], [{'a':['1'], 'b':['2', '3'], 'c':['']}, {'a':[ '2,ab' ], 'b':['1']}])
    assert request.line.uri.path.parts == parts, request.line.uri.path.parts
    assert request.line.uri.path.parts[0].params == params[0]
    assert request.line.uri.path.parts[1].params == params[1]


# Querystring
# ===========

def test_querystring_starts_full():
    querystring = Querystring(b"baz=buz")
    assert querystring == {'baz': [u'buz']}, querystring

def test_querystring_has_raw_set():
    querystring = Querystring(b"baz=buz")
    assert querystring.raw == "baz=buz", querystring.raw

def test_querystring_raw_is_str():
    querystring = Querystring(b"baz=buz")
    assert isinstance(querystring.raw, str)

def test_querystring_has_decoded_set():
    querystring = Querystring(b"baz=buz")
    assert querystring.decoded == u"baz=buz", querystring.decoded

def test_querystring_decoded_is_unicode():
    querystring = Querystring(b"baz=buz")
    assert isinstance(querystring.decoded, unicode)

def test_querystring_unquotes_and_decodes_UTF_8():
    querystring = Querystring(b"baz=%e2%98%84")
    assert querystring.decoded == u"baz=\u2604", querystring.decoded

def test_querystring_comes_out_UTF_8():
    querystring = Querystring(b"baz=%e2%98%84")
    assert querystring['baz'] == u"\u2604", querystring['baz']

def test_querystring_chokes_on_bad_unicode():
    raises(UnicodeDecodeError, Querystring, b"baz=%e2%98")

def test_querystring_unquotes_plus():
    querystring = Querystring("baz=+%2B")
    assert querystring.decoded == u"baz= +", querystring.decoded
    assert querystring['baz'] == " +"


