from aspen import restarter
import dingus
 

def test_startup_basically_works():
    website = dingus.Dingus()
    website.configuration.root = 'foo'
    restarter.startup(website)
    assert 0
