
import time
import os.path
import tempfile

from aspen import resources
from aspen.testing.client import TestClient
from aspen.website import Website


def _writedata(filename, data):
    f = file(filename, 'w')
    f.write(data)
    f.close()

def test_watchdog_basically_works():
    # make temp website to serve out
    www_root = tempfile.mkdtemp('test_watchdog')
    tfbase = 'filea.txt'
    testfile = os.path.join(www_root, tfbase)
    _writedata(testfile, 'valuea')
    website = Website(['-w', www_root] )

    # start a watchdog (normally done in website.start())
    watchdog = resources.watcher_for(www_root)
    watchdog.start()

    # verify the file is served correctly
    client = TestClient(website)
    response = client.get('/'+tfbase )
    assert 'valuea' in response.body, response.body + " didn't contain valuea"

    # now change the file
    _writedata(testfile, 'valueb')
    time.sleep(1)

    # and verify that the file is served correctly again
    response = client.get('/'+tfbase )
    assert 'valueb' in response.body, response.body + " didn't contain valueb"

    watchdog.stop()

