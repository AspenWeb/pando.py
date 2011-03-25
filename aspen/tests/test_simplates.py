from os.path import join

from aspen.http import Response
from aspen.simplates import handle, load_uncached 
from aspen.tests.fsfix import attach_teardown, mk


class StubRequest(object):
    def __init__(self, fs):
        """Takes a path under ./fsfix to a simplate.
        """
        self.root = join('.', 'fsfix')
        self.fs = join('.', 'fsfix', fs)
        self.namespace = {}
        class Foo:
            pass
        self.conf = Foo()
        self.conf.aspen = {}

def Simplate(fs):
    return load_uncached(StubRequest(fs))

def test_barely_working():
    mk(('index.html', "Greetings, program!"))
    simplate = Simplate('index.html')
    actual = simplate[0]
    expected = 'text/html'
    assert actual == expected, actual

def test_handle_barely_working():
    mk(('index.html', "Greetings, program!"))
    request = StubRequest('index.html')
    response = Response()
    handle(request, response)
    actual = response.body
    expected = "Greetings, program!"
    assert actual == expected, actual

attach_teardown(globals())
