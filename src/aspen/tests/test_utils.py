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



# host_middleware
# ===============

def wsgi(environ, start_response):
    start_response('200 OK', [])
    return ["You hit %s." % environ.get('HTTP_HOST', '_______')]

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write


def test_host_middleware_basic():
    mk()
    environ = {'HTTP_HOST':'foo', 'PATH_INFO':'/'}
    expected = ["You hit foo."]
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual

def test_host_middleware_no_HTTP_HOST():
    mk('__', '__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=foo'))
    environ = { 'PATH_INFO':'/'
              , 'wsgi.url_scheme':'http'
               }
    expected = ['You hit foo.']
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual

def test_host_middleware_mismatch():
    mk('__', '__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=foo'))
    environ = { 'HTTP_HOST':'bar:9000'
              , 'wsgi.url_scheme':'http'
               }
    expected = ['Please use http://foo/.']
    actual = u.host_middleware('foo', wsgi)(environ, start_response)
    assert actual == expected, actual




# Remove the filesystem fixture after some tests.
# ===============================================

#attach_rm(globals(), 'test_find_default')
attach_rm(globals(), 'test_check_trailing_slash')
attach_rm(globals(), 'test_host_middleware_')
