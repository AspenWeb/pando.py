from os.path import join, realpath

from aspen._configuration import Configuration
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_rm
from aspen.website import Website as _Website
from aspen.load import Handler


# Fixture
# =======

# Build a simple handler.
# -----------------------

def always_true(fp, pred):
    return True

def handle(environ, start_response):
    start_response('200 OK', [])
    return ["You hit %s." % environ.get('HTTP_HOST', '_______')]

handler = Handler({'foo':always_true}, handle)
handler.add("foo", 0)


# Build a website.
# ----------------

def Website():
    configuration = Configuration(['--root', 'fsfix'])
    configuration.load_plugins()
    configuration.handlers = [handler] # simple handler
    return _Website(configuration)

def start_response(status, headers, exc=None):
    def write():
        return status, headers
    return write


# Tests
# =====

def test_basic():
    mk()
    expected = ['You hit _______.']
    actual = Website()({'PATH_INFO':'/'}, start_response)
    assert actual == expected, actual


attach_rm(globals(), 'test_')