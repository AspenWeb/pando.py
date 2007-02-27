import os
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib
from os.path import isfile, join

import aspen
from aspen._configuration import Configuration
from aspen.exceptions import *
from aspen.tests import BIN_ASPEN, assert_raises
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


# Define a cross-platform kill().
# ===============================
# http://python.org/infogami-faq/windows/how-do-i-emulate-os-kill-in-windows/

if 'win' in sys.platform:
    try:
        import win32api
    except ImportError:
        win32api = None

    def kill(pid, foo):
        # This doesn't trigger a clean shutdown, but we don't really need that
        # here. When we do need that, we'll have implemented Aspen as a
        # service, no?
        if win32api is None:
            raise ImportError( "On MS Windows, this test requires the win32api "
                             + "module, which comes with pywin32: "
                             + "http://sourceforge.net/projects/pywin32/"
                              )
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))
else:
    kill = os.kill


# Tests
# =====

def test_greetings_program():
    """This is also a general smoke test, as it runs the entire Aspen stack.
    """
    mk( 'root', ('root/index.html', "Greetings, program!")
      , ('smoke-it.py', BIN_ASPEN) # simulate bin/aspen
       )
    proc = subprocess.Popen([ 'python' # assumed to be on PATH
                            , join('fsfix', 'smoke-it.py')
                            , '--address', ':53700'
                            , '--root', join('fsfix', 'root')
                            , '--mode', 'production'
                             ])
    time.sleep(1) # give time to startup
    expected = 'Greetings, program!'
    actual = urllib.urlopen('http://localhost:53700/').read()
    kill(proc.pid, signal.SIGTERM)
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


def test_auto_index():
    mk( 'root', 'root/__', 'root/FOO'
      , ('smoke-it.py', BIN_ASPEN) # simulate bin/aspen
       )
    proc = subprocess.Popen([ 'python' # assumed to be on PATH
                            , join('fsfix', 'smoke-it.py')
                            , '--address', ':53700'
                            , '--root', join('fsfix', 'root')
                            , '--mode', 'production'
                             ])
    time.sleep(1) # give time to startup
    actual = urllib.urlopen('http://localhost:53700/').read()
    # @@: how do we check for 200 response code?
    # for now just hit localhost:53700 to test manually
    kill(proc.pid, signal.SIGTERM)
    proc.wait()
    assert 'FOO' in actual
    assert '__' not in actual



attach_rm(globals(), 'test_')