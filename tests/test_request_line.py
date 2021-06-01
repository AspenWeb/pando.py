from pytest import raises

from pando import Response
from pando.http.mapping import Mapping
from pando.http.request import Line, Method, URI, Version, Path, Querystring


def byte(i):
    return bytes(bytearray([i]))


# Line
# ====

def test_line_works():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line == b"GET / HTTP/0.9"

def test_line_has_method():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.method == b"GET"

def test_line_has_uri():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.uri == b"/"

def test_line_has_version():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.version == b"HTTP/0.9"

def test_line_raises_404_on_non_ASCII_in_uri():
    assert raises(Response, Line, b"GET", byte(128), b"HTTP/1.1").value.code == 400


# Method
# ======

def test_method_works():
    method = Method(b"GET")
    assert method == b"GET"

def test_method_is_bytes_subclass():
    method = Method(b"GET")
    assert issubclass(method.__class__, bytes)

def test_method_is_bytes_instance():
    method = Method(b"GET")
    assert isinstance(method, bytes)

def test_method_as_text_works():
    method = Method(b"GET")
    assert method.as_text == "GET"

def test_method_as_text_is_text():
    method = Method(b"GET")
    assert isinstance(method.as_text, str)

def test_method_can_be_OPTIONS(): assert Method(b"OPTIONS") == b"OPTIONS"
def test_method_can_be_GET():     assert Method(b"GET")     == b"GET"
def test_method_can_be_HEAD():    assert Method(b"HEAD")    == b"HEAD"
def test_method_can_be_POST():    assert Method(b"POST")    == b"POST"
def test_method_can_be_PUT():     assert Method(b"PUT")     == b"PUT"
def test_method_can_be_DELETE():  assert Method(b"DELETE")  == b"DELETE"
def test_method_can_be_TRACE():   assert Method(b"TRACE")   == b"TRACE"
def test_method_can_be_CONNECT(): assert Method(b"CONNECT") == b"CONNECT"

def test_method_can_be_big():
    big = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--"
    assert Method(big) == big

def test_method_cant_be_non_ASCII():
    assert raises(Response, Method, b"\x80").value.code == 400

def test_method_can_be_valid_perl():
    assert Method(b"!#$%&'*+-.^_`|~") == b"!#$%&'*+-.^_`|~"

def the400(i):
    assert raises(Response, Method, byte(i)).value.code == 400

# 0-31
def test_method_no_chr_0(): the400(0)
def test_method_no_chr_1(): the400(1)
def test_method_no_chr_2(): the400(2)
def test_method_no_chr_3(): the400(3)
def test_method_no_chr_4(): the400(4)
def test_method_no_chr_5(): the400(5)
def test_method_no_chr_6(): the400(6)
def test_method_no_chr_7(): the400(7)
def test_method_no_chr_8(): the400(8)
def test_method_no_chr_9(): the400(9) # HT

def test_method_no_chr_10(): the400(10)
def test_method_no_chr_11(): the400(11)
def test_method_no_chr_12(): the400(12)
def test_method_no_chr_13(): the400(13)
def test_method_no_chr_14(): the400(14)
def test_method_no_chr_15(): the400(15)
def test_method_no_chr_16(): the400(16)
def test_method_no_chr_17(): the400(17)
def test_method_no_chr_18(): the400(18)
def test_method_no_chr_19(): the400(19)

def test_method_no_chr_20(): the400(20)
def test_method_no_chr_21(): the400(21)
def test_method_no_chr_22(): the400(22)
def test_method_no_chr_23(): the400(23)
def test_method_no_chr_24(): the400(24)
def test_method_no_chr_25(): the400(25)
def test_method_no_chr_26(): the400(26)
def test_method_no_chr_27(): the400(27)
def test_method_no_chr_28(): the400(28)
def test_method_no_chr_29(): the400(29)

def test_method_no_chr_30(): the400(30)
def test_method_no_chr_31(): the400(31)
def test_method_no_chr_32(): the400(32) # space
def test_method_no_chr_33(): assert Method(byte(33)) == b'!'

def test_method_no_chr_40(): the400(40) # (
def test_method_no_chr_41(): the400(41) # )
def test_method_no_chr_60(): the400(60) # <
def test_method_no_chr_62(): the400(62) # >
def test_method_no_chr_64(): the400(64) # @
def test_method_no_chr_44(): the400(44) # ,
def test_method_no_chr_59(): the400(59) # ;
def test_method_no_chr_58(): the400(58) # :
def test_method_no_chr_92(): the400(92) # \
def test_method_no_chr_34(): the400(34) # "
def test_method_no_chr_47(): the400(47) # /
def test_method_no_chr_91(): the400(91) # [
def test_method_no_chr_93(): the400(93) # ]
def test_method_no_chr_63(): the400(63) # ?
def test_method_no_chr_61(): the400(61) # =
def test_method_no_chr_123(): the400(123) # {
def test_method_no_chr_125(): the400(125) # }


# URI
# ===

def test_uri_works_at_all():
    uri = URI(b"/")
    assert uri == b'/'


def test_uri_sets_path():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.path.decoded == "/baz.html", uri.path.decoded

def test_uri_sets_querystring():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.querystring.decoded == "buz=bloo", uri.querystring.decoded


def test_uri_path_mapping():
    uri = URI(b"/baz.html?buz=bloo")
    assert isinstance(uri.path.mapping, Mapping)

def test_uri_querystring_mapping():
    uri = URI(b"/baz.html?buz=bloo")
    assert isinstance(uri.querystring.mapping, Mapping)


def test_uri_normal_case_is_normal():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.path == Path(b"/baz.html")
    assert uri.querystring == Querystring(b"buz=bloo")



# Version
# =======

def test_version_can_be_HTTP_0_9():
    actual = Version(b"HTTP/0.9")
    expected = b"HTTP/0.9"
    assert actual == expected

def test_version_can_be_HTTP_1_0():
    actual = Version(b"HTTP/1.0")
    expected = b"HTTP/1.0"
    assert actual == expected

def test_version_can_be_HTTP_1_1():
    actual = Version(b"HTTP/1.1")
    expected = b"HTTP/1.1"
    assert actual == expected

def test_version_can_be_HTTP_1_2():
    assert Version(b"HTTP/1.2").info == (1, 2)

def test_version_cant_be_junk():
    assert raises(Response, lambda: Version(b"http flah flah").info).value.code == 400

def test_version_cant_even_be_lowercase():
    assert raises(Response, lambda: Version(b"http/1.1").info).value.code == 400

def test_version_with_garbage_is_safe():
    r = raises(Response, lambda: Version(b"HTTP\xef/1.1").info).value
    assert r.code == 400, r.code
    assert r.body == "Bad HTTP version: HTTP\\xef/1.1.", r.body

def test_version_major_is_int():
    version = Version(b"HTTP/1.0")
    expected = 1
    actual = version.major
    assert actual == expected

def test_version_minor_is_int():
    version = Version(b"HTTP/0.9")
    expected = 9
    actual = version.minor
    assert actual == expected

def test_version_info_is_tuple():
    version = Version(b"HTTP/0.9")
    expected = (0, 9)
    actual = version.info
    assert actual == expected

def test_version_is_bytestring():
    version = Version(b"HTTP/0.9")
    assert isinstance(version, bytes)
