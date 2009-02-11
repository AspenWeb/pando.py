from os.path import join, realpath

import aspen
from aspen.tests.fsfix import mk, attach_teardown


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

    aspen.configure(['--root', 'fsfix'])    # can't configure until root exists
    from aspen.handlers import static       # lazy import since we use conf at
                                            #   import-time

    environ = {'PATH_TRANSLATED':realpath(join('fsfix', 'index.html'))}
    expected = 'Foo.'
    actual = static.wsgi(environ, start_response).next()
    assert actual == expected, actual


attach_teardown(globals())
