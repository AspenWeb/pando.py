from aspen.hooks import Hooks
from aspen.testing import assert_raises, attach_teardown


# Fixture
# =======

import random


def test_hooks_is_barely_instantiable():
    actual = Hooks([])
    assert actual == {}, actual

def test_hooks_is_instantiable_with_one_section():
    actual = Hooks(['foo'])
    assert actual == {'foo': []}, actual

def test_hooks_is_not_instantiable_with_str():
    assert_raises(TypeError, Hooks, 'foo')

def test_hooks_is_not_instantiable_with_unicode():
    assert_raises(TypeError, Hooks, 'foo')

def test_hooks_cant_be_subscripted():
    hooks = Hooks(['foo'])
    assert_raises(NotImplementedError, lambda s: hooks[s], 'foo')

def test_hooks_can_be_registered():
    hooks = Hooks(['inbound_early'])
    hooks.inbound_early.register(random.random)
    actual = hooks
    assert actual == {'inbound_early': [random.random]}, actual

def test_non_callables_cant_be_registered():
    hooks = Hooks(['inbound_early'])
    assert_raises(TypeError, hooks.inbound_early.register, None)

def test_hooks_cant_be_appended():
    hooks = Hooks(['inbound_early'])
    assert_raises(NotImplementedError, hooks.inbound_early.append, None)


attach_teardown(globals())
