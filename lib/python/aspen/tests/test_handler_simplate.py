import os.path

from aspen.tests import assert_raises
from aspen.tests.fsfix import mk as _mk
from aspen.tests.fsfix import attach_rm

from aspen.handlers.simplates import wsgi


# Fixture
# =======

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write

def path(*parts):
    """Given relative path parts, convert to absolute path on the filesystem.
    """
    return os.path.realpath(os.path.join(*parts))

def mk(*treedef, **kw):
    """Extend aspen.tests.fsfix.mk to configure for simplates.
    """
    _mk(('__/etc/handlers.conf', """
      catch_all aspen.rules:catch_all

      [aspen.handlers.simplates:wsgi]
      catch_all
    """), *treedef, **kw)


# Tests
# =====

def test_basic():
    mk(('index.html', "Greetings, program!"), configure=True)
    expected = ['Greetings, program!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_two_parts():
    mk(('index.html', "foo='program'\x0cGreetings, %(foo)s!"), configure=True)
    expected = [u'Greetings, program!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_three_parts():
    mk(( 'index.html'
       , "foo='Greetings'\x0cbar='program'\x0c%(foo)s, %(bar)s!"
        ), configure=True)
    expected = [u'Greetings, program!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_namespace_overlap():
    mk(( 'index.html'
       , "foo='perl'\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_namespace_overlap():
    mk(( 'index.html'
       , "foo='perl'\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def _test_SystemExit_first_section(): # this kills the test :)
    mk(( 'index.html'
       , "raise SystemExit\x0cfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, python!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_SystemExit_second_section():
    mk(( 'index.html'
       , "foo='perl'\nraise SystemExit\nfoo='python'\x0cGreetings, %(foo)s!"
        ), configure=True)
    expected = [u'Greetings, perl!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual


def test_explicit_response():
    mk(( 'index.html'
       , "response=[u'Greetings, program!']\x0cblip"
        ), configure=True)
    expected = [u'Greetings, program!']
    actual = wsgi( {'PATH_TRANSLATED':path('fsfix', 'index.html')}
                 , start_response
                  )
    assert actual == expected, actual



# Teardown
# ========

attach_rm(globals(), 'test_')