import os
import signal
import subprocess
import sys
import time
import urllib

from aspen._configuration import Configuration
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
    config.load_plugins()
    return _Website(config)


# Tests
# =====

def test_greetings_program():
    """This is also a general smoke test, as it runs the entire Aspen process.
    """
    mk(('index.html', 'Greetings, program!'))
    proc = subprocess.Popen([ 'aspen'
                            , '--address', ':53700'
                            , '--root', 'fsfix'
                            , '--mode', 'production'
                             ])
    time.sleep(1) # give time to startup
    expected = 'Greetings, program!'
    actual = urllib.urlopen('http://localhost:53700/').read()
    os.kill(proc.pid, signal.SIGTERM)
    proc.wait()
    assert actual == expected, actual

def test_your_first_handler():
    mk( lib_python, '__/etc'
      , (lib_python+'/handy.py', """
def handle(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [environ['PATH_TRANSLATED']]
""")
      , ('__/etc/handlers.conf', """
fnmatch aspen.rules:fnmatch

[handy:handle]
fnmatch *.asp
""")
      , ('handled.asp', "Greetings, program?")
        )

    expected = [os.path.realpath(os.path.join('fsfix', 'handled.asp'))]
    actual = Website()({'PATH_INFO':'handled.asp'}, lambda a,b:a)
    assert actual == expected, actual


attach_rm(globals(), 'test_')