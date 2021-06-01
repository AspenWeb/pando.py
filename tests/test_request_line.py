import pytest
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

def test_method_can_be_OPTIONS():
    assert Method(b"OPTIONS") == b"OPTIONS"

def test_method_can_be_GET():
    assert Method(b"GET") == b"GET"

def test_method_can_be_HEAD():
    assert Method(b"HEAD") == b"HEAD"

def test_method_can_be_POST():
    assert Method(b"POST") == b"POST"

def test_method_can_be_PUT():
    assert Method(b"PUT") == b"PUT"

def test_method_can_be_DELETE():
    assert Method(b"DELETE") == b"DELETE"

def test_method_can_be_TRACE():
    assert Method(b"TRACE") == b"TRACE"

def test_method_can_be_CONNECT():
    assert Method(b"CONNECT") == b"CONNECT"

def test_method_can_be_big():
    big = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz--"
    assert Method(big) == big

def test_method_cant_be_non_ASCII():
    assert raises(Response, Method, b"\x80").value.code == 400

def test_method_can_be_valid_perl():
    assert Method(b"!#$%&'*+-.^_`|~") == b"!#$%&'*+-.^_`|~"

def the400(i):
    assert raises(Response, Method, byte(i)).value.code == 400

@pytest.mark.parametrize('i', range(32))
def test_method_chr_0_to_32(i):
    the400(i)

def test_method_chr_33():
    assert Method(byte(33)) == b'!'

@pytest.mark.parametrize('i', (
    40,   # (
    41,   # )
    60,   # <
    62,   # >
    64,   # @
    44,   # ,
    59,   # ;
    58,   # :
    92,   # \
    34,   # "
    47,   # /
    91,   # [
    93,   # ]
    63,   # ?
    61,   # =
    123,  # {
    125,  # }
))
def test_method_other_forbidden_characters(i):
    the400(i)


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
