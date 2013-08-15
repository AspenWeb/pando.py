import time

from aspen import resources
from aspen.testing.client import TestClient
from aspen.testing.fsfix import fix, FSFIX, mk, attach_teardown
from aspen.website import Website


def test_watchdog_basically_works():
    # make temp website to serve out
    mk(('filea.txt', 'valuea'))
    website = Website(['-w', FSFIX])

    # start a watchdog (normally done in website.start())
    watchdog = resources.watcher_for(FSFIX)
    watchdog.start()

    # verify the file is served correctly
    client = TestClient(website)
    response = client.get('/filea.txt')
    assert 'valuea' in response.body, response.body + " didn't contain valuea"

    # now change the file
    open(fix('filea.txt'), 'w+').write('valueb')
    print fix('filea.txt')
    import os; os.system("cat %s" % fix('filea.txt')); print
    time.sleep(1)

    # and verify that the file is served correctly again
    response = client.get('/filea.txt')
    assert 'valueb' in response.body, response.body + " didn't contain valueb"

    watchdog.stop()


attach_teardown(globals())
