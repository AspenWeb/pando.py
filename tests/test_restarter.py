from aspen import restarter
from aspen.testing.fsfix import attach_teardown

class Foo:
    pass

def test_startup_basically_works():
    website = Foo()
    website.changes_kill = True
    website.root = 'foo'
    website.network_engine = Foo()
    website.network_engine.start_restarter = lambda x: x
    website.configuration_scripts = []
    restarter.install(website)
    expected = set()
    actual = restarter.extras
    assert actual == expected, actual


attach_teardown(globals())
