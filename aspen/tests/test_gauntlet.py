import os.path

from aspen import gauntlet
from aspen.tests.fsfix import mk


class StubRequest:
    def __init__(self, fs):
        self.root = os.path.realpath('fsfix')
        self.fs = fs 


def test_virtual_path_is_virtual():
    mk(('foo.html', "Greetings, program!"))
    request = StubRequest('/foo.html')
    parts = ['', 'foo.html']
    gauntlet.virtual_paths(request, parts)

    expected = os.path.realpath(os.path.join('fsfix', 'foo.html'))
    actual = request.fs
    assert actual == expected, actual

def test_virtual_path_is_virtual():
    mk(('foo.html', "Greetings, program!"))
    request = StubRequest('/foo.html')
    parts = ['', 'foo.html']
    gauntlet.virtual_paths(request, parts)

    expected = os.path.realpath(os.path.join('fsfix', 'foo.html'))
    actual = request.fs
    assert actual == expected, actual
