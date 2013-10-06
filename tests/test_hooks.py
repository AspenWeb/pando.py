from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.hooks import Hooks
from aspen.testing import teardown_function


def test_hooks_is_barely_instantiable():
    actual = Hooks().__class__
    assert actual == Hooks

def test_hooks_can_Be_run():
    hooks = Hooks()
    thing = object()
    hooks.yeah_hook = [lambda thing: thing]
    actual = hooks.run('yeah_hook', thing)
    assert actual is thing



