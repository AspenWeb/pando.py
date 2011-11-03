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
    return HooksConf(chr(12), 'fsfix/.aspen/hooks.conf', *also)


# No hooks configured
# ===================

def test_no_aspen_directory():
    expected = [[], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_no_file():
    mk('.aspen')
    expected = [[], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_empty_file():
    mk('.aspen', ('.aspen/hooks.conf', ''))
    expected = [[], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual


# Hooks configured
# ================

def test_something():
    mk('.aspen', ('.aspen/hooks.conf', 'random:choice'))
    expected = [[random.choice], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_must_be_callable():
    mk('.aspen', ('.aspen/hooks.conf', 'string:digits'))
    err = assert_raises(ConfFileError, load)
    assert err.msg == ("'string:digits' is not callable. [fsfix/.aspen"
                       "/hooks.conf, line 1]"), err.msg

def test_order():
    mk('.aspen', ('.aspen/hooks.conf', 'random:choice\nrandom:seed'))
    expected = [[random.choice, random.seed], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual


# Basics
# ======

def test_blank_lines_skipped():
    mk('.aspen', ('.aspen/hooks.conf', '\n\nrandom:choice\n\n'))
    expected = [[random.choice], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual

def test_comments_ignored():
    mk('.aspen', ('.aspen/hooks.conf', """

        #comment
        random:choice#comment
        random:sample # comments

        """))
    expected = [[random.choice, random.sample], [], [], [], [], []]
    actual = load()
    assert actual == expected, actual


# Outbound
# ========

def test_outbound_section():
    mk('.aspen', ('.aspen/hooks.conf', """

        

        random:choice
        random:sample

        

        random:randint


        """))
    expected = [ []
               , [random.choice, random.sample]
               , [random.randint]
               , []
               , []
               , []
                ]
    actual = load()
    assert actual == expected, actual


def test_caret_L_converted_to_page_break():
    mk('.aspen', ('.aspen/hooks.conf', """

        ^L 

        random:choice
        random:sample

        ^L

        random:randint


        """))
    expected = [ []
               , [random.choice, random.sample]
               , [random.randint]
               , []
               , []
               , []
                ]
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
               , []
               , []
                ]
    actual = load('fsfix/first.conf', 'fsfix/second.conf')
    assert actual == expected, actual


# All Six Sections
# =================

def test_form_feeds_on_same_line():
    mk(('foo.conf', """

        random:choice
        random:sample 
        random:randint
        
        random:random
        random:choice

        random:gauss   random:shuffle  

        Ignored!

        """) )
    expected = [ [random.choice, random.sample]
               , [random.randint]
               , [random.random]
               , [random.choice]
               , [random.gauss]
               , [random.shuffle]
                ]
    actual = load('fsfix/foo.conf')
    assert actual == expected, actual


def test_all_six():
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
               , []
               , []
                ]
    actual = load('fsfix/foo.conf')
    assert actual == expected, actual


def test_equal_sections_dont_screw_up_parsing():
    # https://github.com/whit537/aspen/issues/9
    mk(('hooks.conf', """
        ^L
        # inbound_early
        
        ^L
        # inbound_late
        
        ^L
        # outbound_early
        
        ^L
        # outbound_late
        random:shuffle 
        """))
    expected = [[],[],[],[],[random.shuffle],[]]
    actual = load('fsfix/hooks.conf')
    assert actual == expected, actual


# Remove the filesystem fixture after each test.
# ==============================================

attach_teardown(globals())
