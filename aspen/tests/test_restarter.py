from aspen.server import restarter
from aspen.tests.fsfix import attach_teardown

class Foo:
    pass

def test_startup_basically_works():
    website = Foo()
    website.changes_kill = True
    website.dotaspen = 'bar'
    website.root = 'foo'
    website.engine = Foo()
    website.engine.start_restarter = lambda x: x
    restarter.install(website)
    expected = []
    actual = restarter.extras
    assert actual == expected, actual


attach_teardown(globals())
