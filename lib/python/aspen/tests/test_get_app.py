import os

import aspen
from aspen.load import Mixin as Config
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_teardown
from aspen.website import Website as _Website


# Fixture
# =======

import random

class Foo:
    pass

class DummyServer:
    pass

def Website():
    configuration = aspen.configure(['--root=fsfix'])
    configuration.apps = configuration.load_apps()
    server = DummyServer()
    server.configuration = configuration
    return _Website(server)

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write

TEST_PATH_TRANSLATED = os.path.abspath(os.path.join('fsfix', 'foo'))



# Working
# =======

def test_get_app():
    mk('__', '__/etc', ('__/etc/apps.conf', '/ random:choice'))
    expected = random.choice
    actual = Website().get_app({'PATH_INFO':'/'}, start_response)
    assert actual == expected, actual

def test_get_app_no_app():
    mk()
    expected = None
    actual = Website().get_app({'PATH_INFO':'/'}, start_response)
    assert actual == expected, actual


# environ changes
# ===============
# SCRIPT_NAME, PATH_INFO

def test_get_app_environ_basic():
    mk('__', '__/etc', ('__/etc/apps.conf', '/foo random:choice'))
    env = {'PATH_INFO':'/foo/bar'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '/bar')
               , ('PATH_TRANSLATED', TEST_PATH_TRANSLATED)
               , ('SCRIPT_NAME', '/foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual

def test_get_app_environ_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', '/foo random:choice'))
    env = {'PATH_INFO':'/foo/', 'SERVER_NAME': 'foo'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '/')
               , ('PATH_TRANSLATED', TEST_PATH_TRANSLATED)
               , ('SCRIPT_NAME', '/foo')
               , ('SERVER_NAME', 'foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual

def test_get_app_environ_without_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', '/foo random:choice'))
    env = {'PATH_INFO':'/foo'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '')
               , ('PATH_TRANSLATED', TEST_PATH_TRANSLATED)
               , ('SCRIPT_NAME', '/foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual

def test_get_app_environ_with_slash_and_slash_goes_in_PATH_INFO():
    mk('__', '__/etc', ('__/etc/apps.conf', '/foo/ random:choice'))
    env = {'PATH_INFO':'/foo/bar'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '/bar')
               , ('PATH_TRANSLATED', TEST_PATH_TRANSLATED)
               , ('SCRIPT_NAME', '/foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual

def test_get_app_environ_without_slash_and_slash_goes_in_PATH_INFO():
    mk('__', '__/etc', ('__/etc/apps.conf', '/foo random:choice'))
    env = {'PATH_INFO':'/foo/bar'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '/bar')
               , ('PATH_TRANSLATED', TEST_PATH_TRANSLATED)
               , ('SCRIPT_NAME', '/foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual

def test_get_app_environ_root_app():
    mk('__', '__/etc', ('__/etc/apps.conf', '/ random:choice'))
    env = {'PATH_INFO':'/', 'SERVER_NAME': 'foo'}
    Website().get_app(env, start_response)
    expected = [ ('PATH_INFO', '/')
               , ('PATH_TRANSLATED', os.path.realpath('fsfix'))
               , ('SCRIPT_NAME', '')
               , ('SERVER_NAME', 'foo')
                ]
    actual = list(env.items())
    actual.sort()
    assert actual == expected, actual


# Example in docs
# ===============

EXAMPLE = """

/foo        random:choice   # will get both /foo and /foo/
/bar/       random:sample   # /bar will redirect to /bar/
/bar/baz    random:shuffle  # will 'steal' some of /bar's requests

"""

def test_get_app_doc_example():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = None
    actual = Website().get_app({'PATH_INFO':'/'}, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_foo_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.choice
    environ = {'PATH_INFO':'/foo', 'SERVER_NAME':'foo'}
    actual = Website().get_app(environ, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_foo_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.choice
    actual = Website().get_app({'PATH_INFO':'/foo/'}, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_bar_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    environ = { 'wsgi.url_scheme':'http'
              , 'SERVER_NAME':'foo'
              , 'SERVER_PORT':'80'
              , 'PATH_INFO':'/bar'
               }
    expected = ['Resource moved to: http://foo/bar/']
    actual = Website().get_app(environ, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_bar_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.sample
    actual = Website().get_app({'PATH_INFO':'/bar/'}, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz'}, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz/'}, start_response)
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_with_slash_and_more():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz/buz/biz.html'}, start_response)
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_teardown(globals())
