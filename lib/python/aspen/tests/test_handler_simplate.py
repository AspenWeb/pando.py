import os.path
import time

from aspen.tests import assert_raises
from aspen.tests import fsfix

from aspen.handlers.simplates import stdlib
from aspen.handlers.simplates.base import BaseSimplate


# Fixture
# =======

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write

INDEX_HTML = fsfix.path('fsfix', 'index.html')
WSGI_ARGS = ({'PATH_TRANSLATED':INDEX_HTML}, start_response)

def mk(*treedef, **kw):
    """Extend aspen.tests.fsfix.mk to configure for simplates.
    """
    fsfix.mk(('__/etc/handlers.conf', """
      catch_all aspen.rules:catch_all

      [aspen.handlers.simplates:stdlib]
      catch_all
    """), *treedef, **kw)

def mk_prod(*treedef, **kw):
    """Extend aspen.tests.fsfix.mk to configure for simplates, production mode.
    """
    fsfix.mk(('__/etc/handlers.conf', """
      catch_all aspen.rules:catch_all

      [aspen.handlers.simplates:stdlib]
      catch_all
    """),
    ('__/etc/aspen.conf', "[main]\nmode=production"),
     *treedef, **kw)


# Tests
# =====

def test_basic():
    mk(('index.html', "Greetings, program!"), configure=True)
    expected = ['Greetings, program!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_two_parts():
    mk(('index.html', "foo='program'\x0cGreetings, %(foo)s!"), configure=True)
    expected = [u'Greetings, program!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_three_parts():
    mk(( 'index.html'
       , "foo='Greetings'\x0cbar='program'\x0c%(foo)s, %(bar)s!"
        ), configure=True)
    expected = [u'Greetings, program!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_namespace_overlap():
    mk(( 'index.html'
       , "foo='perl'\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_namespace_overlap():
    mk(( 'index.html'
       , "foo='perl'\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def _test_SystemExit_first_section(): # this kills the test run :)
    mk(( 'index.html'
       , "raise SystemExit\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_SystemExit_second_section():
    mk(( 'index.html'
       , "foo='perl'\nraise SystemExit\nfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, perl!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_explicit_response():
    mk(( 'index.html'
       , "response=[u'Greetings, program!']\x0cblip"
        ), configure=True)
    expected = [u'Greetings, program!']
    actual = stdlib(*WSGI_ARGS)
    assert actual == expected, actual


def test_cache():
    mk_prod(('index.html', "Greetings, perl!"), configure=True)

    cache = BaseSimplate()

    expected = 'Greetings, perl!'
    actual = cache._load_simplate_cached(INDEX_HTML)[2]
    assert actual == expected, actual
    first = cache._BaseSimplate__cache[INDEX_HTML].modtime

    time.sleep(2)
    open(INDEX_HTML, 'w+').write('Greetings, python!')

    expected = 'Greetings, python!'
    actual = cache._load_simplate_cached(INDEX_HTML)[2]
    assert actual == expected, actual
    second = cache._BaseSimplate__cache[INDEX_HTML].modtime

    assert second > first, (first, second)


# Teardown
# ========

fsfix.attach_rm(globals(), 'test_')