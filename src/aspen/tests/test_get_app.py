from aspen.httpy import Response
from aspen.load import Mixin as Config
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_rm
from aspen.website import Website as _Website


# Fixture
# =======

import random

class Foo:
    pass

def Website():
    config = Config()
    config.paths = Foo()
    config.paths.root = 'fsfix'
    config.paths.__ = 'fsfix/__'
    config.apps = config.load_apps()
    return _Website(config)


# Working
# =======

def test_get_app():
    mk('__', '__/etc', ('__/etc/apps.conf', '/ random:choice'))
    expected = random.choice
    actual = Website().get_app({'PATH_INFO':'/'})
    assert actual == expected, actual

def test_get_app_no_app():
    expected = None
    actual = Website().get_app({'PATH_INFO':'/'})
    assert actual == expected, actual


EXAMPLE = """

/foo        random:choice   # will get both /foo and /foo/
/bar/       random:sample   # /bar will redirect to /bar/
/bar/baz    random:shuffle  # will 'steal' some of /bar's requests

"""

def test_get_app_doc_example():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = None
    actual = Website().get_app({'PATH_INFO':'/'})
    assert actual == expected, actual

def test_get_app_doc_example_foo_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.choice
    actual = Website().get_app({'PATH_INFO':'/foo'})
    assert actual == expected, actual

def test_get_app_doc_example_foo_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.choice
    actual = Website().get_app({'PATH_INFO':'/foo/'})
    assert actual == expected, actual

def test_get_app_doc_example_bar_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    environ = dict()
    environ['wsgi.url_scheme'] = 'http'
    environ['HTTP_HOST'] = 'foo'
    environ['PATH_INFO'] = '/bar'
    err = assert_raises(Response, Website().get_app, environ)
    assert err.code == 301, err.code

def test_get_app_doc_example_bar_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.sample
    actual = Website().get_app({'PATH_INFO':'/bar/'})
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_no_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz'})
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_with_slash():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz/'})
    assert actual == expected, actual

def test_get_app_doc_example_bar_baz_with_slash_and_more():
    mk('__', '__/etc', ('__/etc/apps.conf', EXAMPLE))
    expected = random.shuffle
    actual = Website().get_app({'PATH_INFO':'/bar/baz/buz/biz.html'})
    assert actual == expected, actual


# Errors
# ======




# Remove the filesystem fixture after each test.
# ==============================================

attach_rm(globals(), 'test_')