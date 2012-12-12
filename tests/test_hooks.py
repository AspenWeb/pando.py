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

def test_hooks_can_be_mass_registered():
    class MyHooks:
        def inbound_early(self, x):
            return x
        def outbound_late(self, x):
            return x + xx
    hooks = Hooks(['inbound_early', 'inbound_late', 'outbound_early', 'outbound_late'])
    myhooks = MyHooks()
    hooks.register(myhooks)
    assert myhooks.inbound_early in hooks.inbound_early
    assert hooks.inbound_late == []
    assert hooks.outbound_early == []
    assert myhooks.outbound_late in hooks.outbound_late


attach_teardown(globals())
