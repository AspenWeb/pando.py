import dingus
from aspen import restarter
from aspen.tests.fsfix import attach_teardown


def test_startup_basically_works():
    website = dingus.Dingus()
    website.dotaspen = 'bar'
    website.root = 'foo'
    restarter.startup(website)
    expected = []
    actual = restarter.extras
    assert actual == expected, actual


attach_teardown(globals())
