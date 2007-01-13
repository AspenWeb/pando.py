from aspen import utils as u
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_rm


# Fixture
# =======

def function():
    pass

class Class:
    def __call__(self):
        pass
    def call(self):
        pass


# cmp_routines
# ============

def test_cmp_routines_bound_methods():
    assert u.cmp_routines(Class().call, Class().call)

def test_cmp_routines_unbound_methods():
    assert u.cmp_routines(Class.call, Class.call)

def test_cmp_routines_mixed_methods(): # actually, this should probably fail
    assert u.cmp_routines(Class().call, Class.call)

def test_cmp_routines_functions():
    assert u.cmp_routines(function, function)

def test_cmp_routines_classes():
    assert u.cmp_routines(Class, Class)

def test_cmp_routines_instances():
    assert u.cmp_routines(Class(), Class())


def test_cmp_routines_mixed():
    assert not u.cmp_routines(function, Class)

def test_cmp_routines_mixed2():
    assert not u.cmp_routines(function, Class())

def test_cmp_routines_mixed2():
    assert not u.cmp_routines(function, Class.call)

def test_cmp_routines_mixed2():
    assert not u.cmp_routines(function, Class().call)


# find_default
# ============
# I'm thinking we'll expand handlers to handle directories, in which case this
# logic will go in such a rule rather than in the main website call, and these
# tests should go with it.

# def test_find_default():
#     mk(('index.html', ''))
#     expected = 'fsfix/index.html'
#     actual = u.find_default(['index.html'], 'fsfix')
#     assert actual == expected, actual
#
# def test_find_default_non_dir():
#     mk(('foo', ''))
#     expected = 'fsfix/foo'
#     actual = u.find_default(['index.html'], 'fsfix/foo')
#     assert actual == expected, actual
#
# def test_find_default_non_existant():
#     expected = 'fsfix/foo'
#     actual = u.find_default(['index.html'], 'fsfix/foo')
#     assert actual == expected, actual


# find_default errors
# ===================

# def test_find_default_dir_no_default():
#     mk('fsfix')
#
#     err = assert_raises(Response, u.find_default, ['index.htm'], 'fsfix')
#     assert err.code == 403, err.code



# full_url
# ========

def test_full_url_basic():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
               }
    expected = 'http://example.com/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_no_HTTP_HOST():
    environ = { 'wsgi.url_scheme':'http'
              , 'SERVER_NAME':'example.com'
              , 'SERVER_PORT':'53700'
               }
    expected = 'http://example.com:53700/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_empty_HTTP_HOST():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':''
              , 'SERVER_NAME':'example.com'
              , 'SERVER_PORT':'53700'
               }
    expected = 'http://example.com:53700/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_HTTP_HOST_with_port():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com:53700'
               }
    expected = 'http://example.com:53700/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_HTTP_HOST_with_port_and_SERVER_STAR():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com:53700'
              , 'SERVER_NAME':'blahblah'
              , 'SERVER_PORT':'bloobloo'
               }
    expected = 'http://example.com:53700/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_standard_port_elided():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com:80'
               }
    expected = 'http://example.com/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_basic():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/'
               }
    expected = 'http://example.com/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_foo():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/foo'
               }
    expected = 'http://example.com/foo'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_PATH_INFO_basic():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'PATH_INFO':'/'
               }
    expected = 'http://example.com/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_PATH_INFO_bar():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'PATH_INFO':'/bar'
               }
    expected = 'http://example.com/bar'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_and_PATH_INFO():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/foo'
              , 'PATH_INFO':'/bar'
               }
    expected = 'http://example.com/foo/bar'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_and_PATH_INFO():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/foo'
              , 'PATH_INFO':'/bar'
               }
    expected = 'http://example.com/foo/bar'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_QUERY_STRING():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'QUERY_STRING':'baz=buz'
               }
    expected = 'http://example.com/?baz=buz'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_QUERY_STRING_empty():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'QUERY_STRING':''
               }
    expected = 'http://example.com/'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_and_QUERY_STRING():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/foo'
              , 'QUERY_STRING':'baz=buz'
               }
    expected = 'http://example.com/foo?baz=buz'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_PATH_INFO_and_QUERY_STRING():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'PATH_INFO':'/bar'
              , 'QUERY_STRING':'baz=buz'
               }
    expected = 'http://example.com/bar?baz=buz'
    actual = u.full_url(environ)
    assert actual == expected, actual

def test_full_url_with_SCRIPT_NAME_and_PATH_INFO_and_QUERY_STRING():
    environ = { 'wsgi.url_scheme':'http'
              , 'HTTP_HOST':'example.com'
              , 'SCRIPT_NAME':'/foo'
              , 'PATH_INFO':'/bar'
              , 'QUERY_STRING':'baz=buz'
               }
    expected = 'http://example.com/foo/bar?baz=buz'
    actual = u.full_url(environ)
    assert actual == expected, actual


# host_middleware
# ===============

def wsgi(environ, start_response):
    start_response('200 OK', [])
    return ["You hit %s." % environ.get('HTTP_HOST', '_______')]

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write


def test_rm_host_middleware_basic():
    mk()
    environ = {'HTTP_HOST':'foo', 'PATH_INFO':'/'}
    expected = ["You hit foo."]
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual

def test_rm_host_middleware_no_HTTP_HOST():
    mk('__', '__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=foo'))
    environ = { 'PATH_INFO':'/'
              , 'wsgi.url_scheme':'http'
               }
    expected = ['You hit foo.']
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual

def test_rm_host_middleware_mismatch():
    mk('__', '__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=foo'))
    environ = { 'HTTP_HOST':'bar:9000'
              , 'wsgi.url_scheme':'http'
               }
    expected = ['Please use http://foo/.']
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual




# Remove the filesystem fixture after some tests.
# ===============================================

attach_rm(globals(), 'test_rm_')
