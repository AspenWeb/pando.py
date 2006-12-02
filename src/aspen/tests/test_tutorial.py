import os
import sys

from aspen.config import Configuration
from aspen.exceptions import *
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_rm
from aspen.website import Website as _Website


# Fixture
# =======

lib_python = os.path.join('__', 'lib', 'python%s' % sys.version[:3])
sys.path.insert(0, os.path.join('fsfix', lib_python))

class Foo:
    pass

def Website():
    config = Configuration(['-rfsfix'])
    return _Website(config)


# Tests
# =====

def test_greetings_program():
    mk(('index.html', 'Greetings, program!'))

    expected = 'Greetings, program!'
    actual = Website()({'PATH_INFO':'/'}, lambda a,b,c=0:a).read()
    assert actual == expected, actual

#    expected = Response(200, 'Greetings, program!')
#    expected.headers['Content-Type'] = 'text/html'
#    expected.headers['Content-Length'] = 19
#
#    assert 'Last-Modified' in actual.headers
#    del actual.headers['Last-Modified']
#
#    assert actual == expected, actual


def test_python_script():
    mk(('foo.py', 'response = ["Greetings, program!\\n"]'))
    expected = ['Greetings, program!\n']
    actual = Website()({'PATH_INFO':'/foo.py'}, lambda a:a)
    assert actual == expected, actual


def test_your_first_handler():
    mk( lib_python, '__/etc'
      , (lib_python+'/handy.py', """
def handle(environ, start_response):
    return environ['aspen.fp'].name
""")
      , ('__/etc/handlers.conf', """
fnmatch aspen.rules:fnmatch

[handy:handle]
fnmatch *.asp
""")
      , ('handled.asp', "Greetings, program?")
        )

    expected = os.path.realpath(os.path.join('fsfix', 'handled.asp'))
    actual = Website()({'PATH_INFO':'handled.asp'}, lambda a:a)
    assert actual == expected, actual


attach_rm(globals(), 'test_')