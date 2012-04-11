from aspen import Response
from aspen.http.mapping import Mapping
from aspen.http.request import Line, Method, URL, Version, Path, Querystring
from aspen.testing import assert_raises


# Line
# ====

def test_line_works():
    line = Line("GET", "/", "HTTP/0.9")
    assert line == u"GET / HTTP/0.9", line

def test_line_has_method():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.method == u"GET", line.method

def test_line_has_url():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.url == u"/", line.url

def test_line_has_version():
    line = Line("GET", "/", "HTTP/0.9")
    assert line.version == u"HTTP/0.9", line.version

def test_line_handles_UTF_8_in_method():
    line = Line("\xe2\x98\x84", "/", "HTTP/1.1")
    assert line.method == u"\u2604", line.method

def test_line_raw_is_bytes():
    line = Line("\xe2\x98\x84", "/", "HTTP/1.1")
    assert line.raw == "\xe2\x98\x84 / HTTP/1.1", line.raw

def test_line_chokes_on_non_ASCII_in_url():
    assert_raises(UnicodeDecodeError, Line, "GET", chr(128), "HTTP/1.1")


# Method
# ======

def test_method_works():
    method = Method("GET")
    assert method == u"GET", method

def test_method_is_unicode_subclass():
    method = Method("GET")
    assert issubclass(method.__class__, unicode), method.__class__

def test_method_is_unicode_instance():
    method = Method("GET")
    assert isinstance(method, unicode), method

def test_method_is_basestring_instance():
    method = Method("GET")
    assert isinstance(method, basestring), method

def test_method_raw_works():
    method = Method("GET")
    assert method.raw == "GET", method.raw

def test_method_raw_is_bytestring():
    method = Method("GET")
    assert isinstance(method.raw, str), method.raw

def test_method_cant_have_more_attributes():
    method = Method("GET")
    assert_raises(AttributeError, setattr, method, "foo", "bar")


# URL
# ===

def test_url_works_at_all():
    url = URL("/")
    expected = u"/"
    actual = url
    assert actual == expected, actual


def test_url_sets_scheme():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.scheme == u"http", url.scheme

def test_url_sets_username():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.username == u"foobar", url.username

def test_url_sets_password():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.password == u"secret", url.password

def test_url_sets_host():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.host == u"www.example.com", url.host

def test_url_sets_port():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.port == 8080, url.port

def test_url_sets_path():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.path.decoded == u"/baz.html", url.path.decoded

def test_url_sets_querystring():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.querystring.decoded == u"buz=bloo", url.querystring.decoded


def test_url_scheme_is_unicode():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.scheme, unicode)

def test_url_username_is_unicode():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.username, unicode)

def test_url_password_is_unicode():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.password, unicode)

def test_url_host_is_unicode():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.host, unicode)

def test_url_port_is_int():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.port, int)

def test_url_path_is_Mapping():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.path, Mapping)

def test_url_querystring_is_Mapping():
    url = URL("http://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert isinstance(url.querystring, Mapping)


def test_url_empty_scheme_is_empty_unicode():
    url = URL("://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.scheme == u"", url.scheme
    assert isinstance(url.scheme, unicode), url.scheme.__class__

def test_url_empty_username_is_empty_unicode():
    url = URL("http://:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.username == u"", url.username
    assert isinstance(url.username, unicode), url.username.__class__

def test_url_empty_password_is_empty_unicode():
    url = URL("http://foobar:@www.example.com:8080/baz.html?buz=bloo")
    assert url.password == u"", url.password
    assert isinstance(url.password, unicode), url.password.__class__

def test_url_empty_host_is_empty_unicode():
    url = URL("http://foobar:secret@:8080/baz.html?buz=bloo")
    assert url.host == u"", url.host
    assert isinstance(url.host, unicode), url.host.__class__

def test_url_empty_port_is_None():
    url = URL("://foobar:secret@www.example.com:8080/baz.html?buz=bloo")
    assert url.port is None, url.port


def test_url_normal_case_is_normal():
    url = URL("/baz.html?buz=bloo")
    assert url.path == Path("/baz.html")
    assert url.querystring == Querystring("buz=bloo")


def test_url_ASCII_worketh():
    url = URL(chr(127))
    assert url == unichr(127), url

def test_url_non_ASCII_worketh_not():
    assert_raises(UnicodeDecodeError, URL, chr(128))

def test_url_encoded_username_is_unencoded_properly():
    url = URL("http://%e2%98%84:secret@www.example.com/foo.html")
    assert url.username == u'\u2604', url.username

def test_url_encoded_password_is_unencoded_properly():
    url = URL("http://foobar:%e2%98%84@www.example.com/foo.html")
    assert url.password == u'\u2604', url.password

def test_url_international_domain_name_comes_out_properly():
    url = URL("http://www.xn--cev.tk/foo.html")
    assert url.host == u'www.\u658b.tk', url.host

def test_url_bad_international_domain_name_raises_UnicodeError():
    assert_raises(UnicodeError, URL, "http://www.xn--ced.tk/foo.html")

def test_url_raw_is_available_on_something():
    url = URL("http://www.xn--cev.tk/")
    assert url.host.raw == "www.xn--cev.tk", url.host.raw



# Version
# =======

def test_version_can_be_HTTP_0_9():
    actual = Version("HTTP/0.9")
    expected = u"HTTP/0.9"
    assert actual == expected, actual

def test_version_can_be_HTTP_1_0():
    actual = Version("HTTP/1.0")
    expected = u"HTTP/1.0"
    assert actual == expected, actual

def test_version_can_be_HTTP_1_1():
    actual = Version("HTTP/1.1")
    expected = u"HTTP/1.1"
    assert actual == expected, actual

def test_version_cant_be_HTTP_1_2():
    assert_raises(Response, Version, "HTTP/1.2")

def test_version_major_is_int():
    version = Version("HTTP/1.0")
    expected = 1
    actual = version.major
    assert actual == expected, actual

def test_version_major_is_int():
    version = Version("HTTP/0.9")
    expected = 9
    actual = version.minor
    assert actual == expected, actual

def test_version_info_is_tuple():
    version = Version("HTTP/0.9")
    expected = (0, 9)
    actual = version.info
    assert actual == expected, actual

def test_version_raw_is_bytestring():
    version = Version("HTTP/0.9")
    expected = str
    actual = version.raw.__class__
    assert actual is expected, actual


# Path
# ====

def test_path_starts_empty():
    path = Path("/bar.html")
    assert path == {}, path

def test_path_has_raw_set():
    path = Path("/bar.html")
    assert path.raw == "/bar.html", path.raw

def test_path_raw_is_str():
    path = Path("/bar.html")
    assert isinstance(path.raw, str)

def test_path_has_decoded_set():
    path = Path("/bar.html")
    assert path.decoded == u"/bar.html", path.decoded

def test_path_decoded_is_unicode():
    path = Path("/bar.html")
    assert isinstance(path.decoded, unicode)

def test_path_unquotes_and_decodes_UTF_8():
    path = Path("/%e2%98%84.html")
    assert path.decoded == u"/\u2604.html", path.decoded

def test_path_doesnt_unquote_plus():
    path = Path("/+%2B.html")
    assert path.decoded == u"/++.html", path.decoded


# Querystring
# ===========

def test_querystring_starts_full():
    querystring = Querystring("baz=buz")
    assert querystring == {'baz': [u'buz']}, querystring

def test_querystring_has_raw_set():
    querystring = Querystring("baz=buz")
    assert querystring.raw == "baz=buz", querystring.raw

def test_querystring_raw_is_str():
    querystring = Querystring("baz=buz")
    assert isinstance(querystring.raw, str)

def test_querystring_has_decoded_set():
    querystring = Querystring("baz=buz")
    assert querystring.decoded == u"baz=buz", querystring.decoded

def test_querystring_decoded_is_unicode():
    querystring = Querystring("baz=buz")
    assert isinstance(querystring.decoded, unicode)

def test_querystring_unquotes_and_decodes_UTF_8():
    querystring = Querystring("baz=%e2%98%84")
    assert querystring.decoded == u"baz=\u2604", querystring.decoded

def test_querystring_comes_out_UTF_8():
    querystring = Querystring("baz=%e2%98%84")
    assert querystring['baz'] == u"\u2604", querystring['baz']

def test_querystring_chokes_on_bad_unicode():
    assert_raises(UnicodeDecodeError, Querystring, "baz=%e2%98")

def test_querystring_unquotes_plus():
    querystring = Querystring("baz=+%2B")
    assert querystring.decoded == u"baz= +", querystring.decoded
