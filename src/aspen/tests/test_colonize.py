from aspen.colon import *
from aspen.tests import assert_raises as _assert_raises


def assert_raises(name, Err):
    _assert_raises(Err, colonize, name, 'filename', 0)


# Working
# =======

def test_basic():
    from random import choice as expected
    actual = colonize('random:choice', 'filename', 0)
    assert actual is expected

def test_dotted_name():
    from email.Message import Message as expected
    actual = colonize('email.Message:Message', 'filename', 0)
    assert actual is expected

def test_dotted_object():
    from random import SystemRandom
    expected = SystemRandom.__init__
    actual = colonize('random:SystemRandom.__init__', 'filename', 0)
    assert actual == expected

def test_dotted_both():
    from email.Message import Message
    expected = Message.__init__
    actual = colonize('email.Message:Message.__init__', 'filename', 0)
    assert actual == expected


# Errors
# ======

def test_must_have_colon():
    assert_raises('foo.bar', ColonizeBadColonsError)

def test_but_only_one_colon():
    assert_raises('foo.bar:baz:buz', ColonizeBadColonsError)

def test_module_name():
    assert_raises('foo.bar; import os; os.remove();:', ColonizeBadModuleError)

def test_module_not_there():
    assert_raises('foo.bar:baz', ColonizeImportError)

def test_object_name():
    assert_raises('string:baz; import os; os.remove();', ColonizeBadObjectError)

def test_object_not_there():
    assert_raises('string:foo', ColonizeAttributeError)

def test_nested_object_not_there():
    assert_raises('string:digits.duggems', ColonizeAttributeError)
