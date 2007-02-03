from os.path import join, realpath

from aspen.handlers.static import static
from aspen.tests.fsfix import mk, attach_rm


# Fixture
# =======

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write


# Tests
# =====

def test_basic():
    mk(('index.html', "Foo."))
    environ = {'PATH_TRANSLATED':realpath(join('fsfix', 'index.html'))}
    expected = 'Foo.'
    actual = static(environ, start_response).next()
    assert actual == expected, actual


attach_rm(globals(), 'test_')