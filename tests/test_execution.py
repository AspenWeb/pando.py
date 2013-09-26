from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import execution
from aspen.testing.fsfix import teardown_function

class Foo:
    pass

def test_startup_basically_works():
    website = Foo()
    website.changes_kill = True
    website.root = 'foo'
    website.network_engine = Foo()
    website.network_engine.start_checking = lambda x: x
    website.configuration_scripts = []
    execution.install(website)
    expected = set()
    actual = execution.extras
    assert actual == expected, repr(actual) + " instead of " + repr(expected)



