import os
import sys

from aspen import load
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

MODULE = """\
class App:
  def __init__(self, website):
    self.website = website
  def __call__(self, env, start):
    return "Greetings, program!"

class AppNoArgs:
  def __call__(self, env, start):
    return "Greetings, program!"
"""


# No middleware configured
# ========================

def test_no_magic_directory():
    loader = Loader()
    loader.paths.__ = None
    expected = []
    actual = loader.load_middleware()
    assert actual == expected, actual

def test_no_file():
    mk('__/etc')
    expected = []
    actual = Loader().load_middleware()
    assert actual == expected, actual

def test_empty_file():
    mk('__/etc', ('__/etc/middleware.conf', ''))
    expected = []
    actual = Loader().load_apps()
    assert actual == expected, actual


# Middleware configured
# =====================

def test_something():
    mk('__/etc', ('__/etc/middleware.conf', 'random:choice'))
    loader = Loader()
    expected = [random.choice]
    actual = Loader().load_middleware()
    assert actual == expected, actual

def test_must_be_callable():
    mk('__/etc', ('__/etc/middleware.conf', 'string:digits'))
    err = assert_raises(MiddlewareConfError, Loader().load_middleware)
    assert err.msg == "'string:digits' is not callable"

def test_order():
    mk('__/etc', ('__/etc/middleware.conf', 'random:choice\nrandom:seed'))
    expected = [random.seed, random.choice]
    actual = Loader().load_middleware()
    assert actual == expected, actual


# Basics
# ======

def test_blank_lines_skipped():
    mk('__/etc', ('__/etc/middleware.conf', '\n\nrandom:choice\n\n'))
    expected = [random.choice]
    actual = Loader().load_middleware()
    assert actual == expected, actual

def test_comments_ignored():
    mk('__/etc', ('__/etc/middleware.conf', """

        #comment
        random:choice#comment
        random:sample # comments

        """))
    expected = [random.sample, random.choice]
    actual = Loader().load_middleware()
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_rm(globals(), 'test_')