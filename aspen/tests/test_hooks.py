import os
import sys

from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_teardown
from aspen.configuration.exceptions import *
from aspen.configuration.hooks import HooksConf


# Fixture
# =======

import random
import string

lib_python = os.path.join('.aspen', 'lib', 'python%s' % sys.version[:3])
sys.path.insert(0, os.path.join('fsfix', lib_python))

class Paths:
    pass

def load(*also):
    return HooksConf('fsfix/.aspen/etc/hooks.conf', *also)


# No hooks configured
# ===================

def test_no_aspen_directory():
    expected = [[], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_no_file():
    mk('.aspen/etc')
    expected = [[], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_empty_file():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', ''))
    expected = [[], [], [], []]
    actual = load()
    assert actual == expected, actual


# Hooks configured
# ================

def test_something():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', 'random:choice'))
    expected = [[random.choice], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_must_be_callable():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', 'string:digits'))
    err = assert_raises(ConfFileError, load)
    assert err.msg == ("On line 1 of fsfix/.aspen/etc/hooks.conf, "
                       "'string:digits' is not callable."), err.msg

def test_order():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', 'random:choice\nrandom:seed'))
    expected = [[random.choice, random.seed], [], [], []]
    actual = load()
    assert actual == expected, actual


# Basics
# ======

def test_blank_lines_skipped():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', '\n\nrandom:choice\n\n'))
    expected = [[random.choice], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_comments_ignored():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', """

        #comment
        random:choice#comment
        random:sample # comments

        """))
    expected = [[random.choice, random.sample], [], [], []]
    actual = load()
    assert actual == expected, actual


# Outbound
# ========

def test_outbound_section():
    mk('.aspen/etc', ('.aspen/etc/hooks.conf', """

        

        random:choice
        random:sample

        

        random:randint


        """))
    expected = [[], [random.choice, random.sample], [random.randint], []]
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
    expected = [ []
               , [random.choice, random.sample, random.random, random.gauss]
               , [random.randint, random.choice, random.shuffle]
               , []
                ]
    actual = load('fsfix/first.conf', 'fsfix/second.conf')
    assert actual == expected, actual


# All Four Sections
# =================

def test_all_four():
    mk(('foo.conf', """

        random:choice
        random:sample 
        random:randint
        
        random:random
        random:gauss
        random:choice
        random:shuffle

        

        Ignored!

        """) )
    expected = [ [random.choice, random.sample]
               , [random.randint]
               , [random.random, random.gauss]
               , [random.choice, random.shuffle]
                ]
    actual = load('fsfix/foo.conf')
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_teardown(globals())
