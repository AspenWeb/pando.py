from aspen import restarter
import dingus
import diesel


diesel.runtime.current_app = dingus.Dingus()
 

def test_startup_basically_works():
    website = dingus.Dingus()
    website.configuration.root = 'foo'
    restarter.startup(website)
    expected = []
    actual = restarter.extras
    assert actual == expected, actual
