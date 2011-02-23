import os
import sys

from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_teardown
from aspen.configuration.exceptions import *
from aspen.configuration.middleware import load_middleware


# Fixture
# =======

import random
import string

lib_python = os.path.join('.aspen', 'lib', 'python%s' % sys.version[:3])
sys.path.insert(0, os.path.join('fsfix', lib_python))

class Paths:
    pass

def load(*also):
    return load_middleware('fsfix/.aspen/etc/middleware.conf', *also)


# No middleware configured
# ========================

def test_no_aspen_directory():
    expected = [[], []]
    actual = load()
    assert actual == expected, actual

def test_no_file():
    mk('.aspen/etc')
    expected = [[], []]
    actual = load()
    assert actual == expected, actual

def test_empty_file():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', ''))
    expected = [[], []]
    actual = load()
    assert actual == expected, actual


# Middleware configured
# =====================

def test_something():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', 'random:choice'))
    expected = [[random.choice], []]
    actual = load()
    assert actual == expected, actual

def test_must_be_callable():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', 'string:digits'))
    err = assert_raises(ConfFileError, load)
    assert err.msg == ("On line 1 of fsfix/.aspen/etc/middleware.conf, "
                       "'string:digits' is not callable."), err.msg

def test_order():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', 'random:choice\nrandom:seed'))
    expected = [[random.choice, random.seed], []]
    actual = load()
    assert actual == expected, actual


# Basics
# ======

def test_blank_lines_skipped():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', '\n\nrandom:choice\n\n'))
    expected = [[random.choice], []]
    actual = load()
    assert actual == expected, actual

def test_comments_ignored():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', """

        #comment
        random:choice#comment
        random:sample # comments

        """))
    expected = [[random.choice, random.sample], []]
    actual = load()
    assert actual == expected, actual


# Outbound
# ========

def test_outbound_section():
    mk('.aspen/etc', ('.aspen/etc/middleware.conf', """

        random:choice
        random:sample

        

        random:randint

        

        ignored!

        """))
    expected = [[random.choice, random.sample], [random.randint]]
    actual = load()
    assert actual == expected, actual


# Layering
# ========

def test_layering():
    mk(('first.conf', """

        random:choice
        random:sample
        random:randint

        """),
       ('second.conf', """

        random:random
        random:gauss
        random:choice
        random:shuffle

        """) )
    expected = [ [random.choice, random.sample, random.random, random.gauss]
               , [random.randint, random.choice, random.shuffle]
                ]
    actual = load('fsfix/first.conf', 'fsfix/second.conf')
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_teardown(globals())
