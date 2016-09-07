from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import text_type

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
    assert line == "GET / HTTP/0.9"

def test_line_has_method():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.method == "GET"

def test_line_has_uri():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.uri == "/"

def test_line_has_version():
    line = Line(b"GET", b"/", b"HTTP/0.9")
    assert line.version == "HTTP/0.9"

def test_line_chokes_on_non_ASCII_in_uri():
    raises(UnicodeDecodeError, Line, b"GET", byte(128), b"HTTP/1.1")


# Method
# ======

def test_method_works():
    method = Method(b"GET")
    assert method == "GET"

def test_method_is_unicode_subclass():
    method = Method(b"GET")
    assert issubclass(method.__class__, text_type)

def test_method_is_unicode_instance():
    method = Method(b"GET")
    assert isinstance(method, text_type)

def test_method_raw_works():
    method = Method(b"GET")
    assert method.raw == b"GET"

def test_method_raw_is_bytestring():
    method = Method(b"GET")
    assert isinstance(method.raw, bytes)

def test_method_cant_have_more_attributes():
    method = Method(b"GET")
    raises(AttributeError, setattr, method, "foo", "bar")

def test_method_can_be_OPTIONS(): assert Method(b"OPTIONS") == "OPTIONS"
def test_method_can_be_GET():     assert Method(b"GET")     == "GET"
def test_method_can_be_HEAD():    assert Method(b"HEAD")    == "HEAD"
def test_method_can_be_POST():    assert Method(b"POST")    == "POST"
def test_method_can_be_PUT():     assert Method(b"PUT")     == "PUT"
def test_method_can_be_DELETE():  assert Method(b"DELETE")  == "DELETE"
def test_method_can_be_TRACE():   assert Method(b"TRACE")   == "TRACE"
def test_method_can_be_CONNECT(): assert Method(b"CONNECT") == "CONNECT"

def test_method_can_be_big():
    big = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--"
    assert Method(big).raw == big

def test_method_we_cap_it_at_64_bytes_just_cause____I_mean___come_on___right():
    big = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--!"
    assert raises(Response, Method, big).value.code == 501

def test_method_cant_be_non_ASCII():
    assert raises(Response, Method, b"\x80").value.code == 501

def test_method_can_be_valid_perl():
    assert Method(b"!#$%&'*+-.^_`|~") == "!#$%&'*+-.^_`|~"

def the501(i):
    assert raises(Response, Method, byte(i)).value.code == 501

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
def test_method_no_chr_9(): the501(9) # HT

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
def test_method_no_chr_33(): assert Method(byte(33)) == '!'

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


# URI
# ===

def test_uri_works_at_all():
    uri = URI(b"/")
    expected = "/"
    actual = uri
    assert actual == expected


def test_uri_sets_path():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.path.decoded == "/baz.html", uri.path.decoded

def test_uri_sets_querystring():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.querystring.decoded == "buz=bloo", uri.querystring.decoded


def test_uri_path_is_Mapping():
    uri = URI(b"/baz.html?buz=bloo")
    assert isinstance(uri.path, Mapping)

def test_uri_querystring_is_Mapping():
    uri = URI(b"/baz.html?buz=bloo")
    assert isinstance(uri.querystring, Mapping)


def test_uri_normal_case_is_normal():
    uri = URI(b"/baz.html?buz=bloo")
    assert uri.path == Path("/baz.html")
    assert uri.querystring == Querystring("buz=bloo")



# Version
# =======

def test_version_can_be_HTTP_0_9():
    actual = Version(b"HTTP/0.9")
    expected = "HTTP/0.9"
    assert actual == expected

def test_version_can_be_HTTP_1_0():
    actual = Version(b"HTTP/1.0")
    expected = "HTTP/1.0"
    assert actual == expected

def test_version_can_be_HTTP_1_1():
    actual = Version(b"HTTP/1.1")
    expected = "HTTP/1.1"
    assert actual == expected

def test_version_cant_be_HTTP_1_2():
    assert raises(Response, Version, b"HTTP/1.2").value.code == 505

def test_version_cant_be_junk():
    assert raises(Response, Version, b"http flah flah").value.code == 400

def test_version_cant_even_be_lowercase():
    assert raises(Response, Version, b"http/1.1").value.code == 400

def test_version_with_garbage_is_safe():
    r = raises(Response, Version, b"HTTP\xef/1.1").value
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

def test_version_raw_is_bytestring():
    version = Version(b"HTTP/0.9")
    expected = bytes
    actual = version.raw.__class__
    assert actual is expected
