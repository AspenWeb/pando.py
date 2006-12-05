import os
import sys

from aspen import handlers, load, rules
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_rm
from aspen.exceptions import *


# Fixture
# =======

import random
import string

lib_python = os.path.join('__', 'lib', 'python%s' % sys.version[:3])
sys.path.insert(0, os.path.join('fsfix', lib_python))

class Paths:
    pass

def Loader():
    """Convenience constructor.
    """
    loader = load.Mixin()
    loader.paths = Paths()
    loader.paths.root = os.path.realpath('fsfix')
    loader.paths.__ = os.path.realpath('fsfix/__')
    return loader

handler = load.Handler({'fnmatch':rules.fnmatch}, random.choice)
handler.add("fnmatch *", 0)

rulefuncs = dict()
rulefuncs['catch_all'] = rules.catch_all
rulefuncs['isdir'] = rules.isdir
rulefuncs['isfile'] = rules.isfile
rulefuncs['fnmatch'] = rules.fnmatch
rulefuncs['hashbang'] = rules.hashbang

http404 = load.Handler(rulefuncs, handlers.HTTP404)
http404.add("isfile", 0)
http404.add("AND fnmatch *.py[cod]", 0)

pyscript = load.Handler(rulefuncs, handlers.pyscript)
pyscript.add("isfile", 0)
pyscript.add("AND fnmatch *.py", 0)
pyscript.add("OR hashbang", 0)

dirsmarts = load.Handler(rulefuncs, handlers.default_or_autoindex)
dirsmarts.add("isdir", 0)

static = load.Handler(rulefuncs, handlers.static)
static.add("catch_all", 0)

DEFAULTS = [http404, pyscript, dirsmarts, static]

MODULE = """\
class Rule:
  def __init__(self, website):
    self.website = website
  def __call__(self, path, predicate):
    return True

class App:
  def __init__(self, website):
    self.website = website
  def __call__(self, env, start):
    return "Greetings, program!"
"""


# Working
# =======

def test_basic():
    mk('__/etc', ('__/etc/handlers.conf', """

        fnmatch aspen.rules:fnmatch

        [random:choice]
        fnmatch *

        """))
    expected = [handler]
    actual = Loader().load_handlers()
    assert actual == expected, actual

def test_classes_instantiated():
    mk( '__/etc', lib_python
      , ('__/etc/handlers.conf', """
            foo TESTING_handlers:Rule
            [TESTING_handlers:App]
            foo *
            """)
      , (lib_python+'/TESTING_handlers.py', MODULE)
       )
    from TESTING_handlers import App, Rule
    handlers = Loader().load_handlers()

    expected = App
    actual = handlers[0].handle.__class__
    assert actual == expected, actual

    expected = Rule
    actual = handlers[0]._funcs['foo'].__class__
    assert actual == expected, actual


# No handlers configured
# ======================
# Should get defaults when there's no file, an empty list when there's an empty
# file.

def test_no_magic_directory():
    loader = Loader()
    loader.paths.__ = None
    expected = DEFAULTS
    actual = loader.load_handlers()
    assert actual == expected, actual

def test_no_file():
    mk('__/etc')
    expected = DEFAULTS
    actual = Loader().load_handlers()
    assert actual == expected, actual

def test_empty_file():
    mk('__/etc', ('__/etc/handlers.conf', ''))
    expected = []
    actual = Loader().load_handlers()
    assert actual == expected, actual



# Errors
# ======

def test_anon_bad_line():
    mk('__/etc', ('__/etc/handlers.conf', 'foo\n[foo]'))
    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "malformed line (no space): 'foo'", err.msg

def test_anon_not_callable():
    mk('__/etc', ('__/etc/handlers.conf', 'foo string:digits'))
    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "'string:digits' is not callable", err.msg


def test_section_bad_section_header():
    mk('__/etc', ('__/etc/handlers.conf', '[foo'))
    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "missing end-bracket", err.msg

def test_section_no_rules_yet():
    mk('__/etc', ('__/etc/handlers.conf', '[foo]'))
    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "no rules specified yet", err.msg

def test_section_not_callable():
    mk('__/etc', ('__/etc/handlers.conf', """

        foo random:choice

        [string:digits]
        foo

        """))

    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "'string:digits' is not callable", err.msg



# Basics
# ======
# Blank lines and comments are tested in the default file.


# Remove the filesystem fixture after each test.
# ==============================================

attach_rm(globals(), 'test_')