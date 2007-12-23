import os
import sys

from aspen import load, rules, configure, unconfigure
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


# Defaults
# --------

def DEFAULTS():
    """Lazy so we have a chance to call aspen.configure().
    """
    from aspen.handlers import static

    rulefuncs = dict()
    rulefuncs['catch_all'] = rules.catch_all

    static = load.Handler(rulefuncs, static.wsgi)
    static.add("catch_all", 0)

    return [static]


# Doc example
# -----------

DOC_EXAMPLE_CONF = """\
catch_all   aspen.rules:catch_all
isfile      aspen.rules:isfile
fnmatch     aspen.rules:fnmatch


# Set up scripts.
# ===============

[aspen.handlers.simplates:stdlib]
    isfile
AND fnmatch *.html


# Everything else is served statically.
# =====================================

[aspen.handlers.static:wsgi]
  catch_all
"""

def DOC_EXAMPLE():
    """Lazy so we can call aspen.configure() first.
    """
    from aspen.handlers import simplates, static

    rulefuncs = dict()
    rulefuncs['catch_all'] = rules.catch_all
    rulefuncs['isfile'] = rules.isfile
    rulefuncs['fnmatch'] = rules.fnmatch

    simplate = load.Handler(rulefuncs, simplates.stdlib)
    simplate.add("isfile", 0)
    simplate.add("AND fnmatch *.html", 0)

    static = load.Handler(rulefuncs, static.wsgi)
    static.add("catch_all", 0)

    return [script, static]


# Working
# =======

def test_basic():
    mk('__/etc', ('__/etc/handlers.conf', """

        fnmatch aspen.rules:fnmatch

        [random:choice]
        fnmatch *

        """))
    handler = load.Handler({'fnmatch':rules.fnmatch}, random.choice)
    handler.add("fnmatch *", 0)
    expected = [handler]
    actual = Loader().load_handlers()
    assert actual == expected, actual


# No handlers configured
# ======================
# Should get defaults when there's no file, an empty list when there's an empty
# file.

def test_no_magic_directory():
    mk()
    configure(['-rfsfix'])
    try:
        loader = Loader()
        loader.paths.__ = None
        expected = DEFAULTS()
        actual = loader.load_handlers()
        assert actual == expected, actual
    finally:
        unconfigure()

def test_no_file():
    mk('__/etc')
    expected = DEFAULTS()
    actual = Loader().load_handlers()
    assert actual == expected, actual

def test_empty_file():
    mk('__/etc', ('__/etc/handlers.conf', ''))
    expected = []
    actual = Loader().load_handlers()
    assert actual == expected, actual

def test_doc_example():
    mk('__/etc', ('__/etc/handlers.conf', DOC_EXAMPLE_CONF))
    configure(['-rfsfix'])
    try:
        expected = DOC_EXAMPLE()
        actual = Loader().load_handlers()
        assert actual == expected, actual
    finally:
        unconfigure()


# Errors
# ======

def test_anon_no_whitespace():
    mk('__/etc', ('__/etc/handlers.conf', 'foo\n[foo]'))
    err = assert_raises(HandlersConfError, Loader().load_handlers)
    assert err.msg == "malformed line (no whitespace): 'foo'", err.msg

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

def test_anon_tab_ok():
    mk('__/etc', ( '__/etc/handlers.conf'
                 , 'foo\taspen.rules:fnmatch\n[random:choice]'
                  ))
    expected = [load.Handler({'foo':rules.fnmatch}, random.choice)]
    actual = Loader().load_handlers()
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_rm(globals(), 'test_')
