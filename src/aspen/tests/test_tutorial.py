import os
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib
from os.path import join

import aspen
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
      , ('smoke-it.py', "import aspen; aspen.main()") # simulate bin/aspen
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


# Another top-level test
# ======================

def test_daemon():
    if 'win' in sys.platform:
        return # don't bother running this test on Windows

    mk( 'root', 'root/__', ('root/index.html', "Greetings, program!")
      , ('smoke-it.py', "import aspen; aspen.main()") # simulate bin/aspen
       )


    # Start the daemon.
    # =================

    proc = subprocess.Popen([ 'python' # assumed to be on PATH
                            , join('fsfix', 'smoke-it.py')
                            , '--address', ':53700'
                            , '--root', join('fsfix', 'root')
                            , 'start'
                             ])
    time.sleep(1) # give time to startup
    expected = 'Greetings, program!'
    actual = urllib.urlopen('http://localhost:53700/').read()
    assert actual == expected, actual # site running


    # Check pidfile permissions.
    # ==========================

    actual = stat.S_IMODE(os.stat('fsfix/root/__/var/aspen.pid')[stat.ST_MODE])
    expected = 0600
    assert actual == expected, actual


    # Check logfile permissions.
    # ==========================

    actual = stat.S_IMODE(os.stat('fsfix/root/__/var/aspen.log')[stat.ST_MODE])
    expected = 0600
    assert actual == expected, actual


    # Stop the daemon.
    # ================

    proc = subprocess.Popen([ 'python' # assumed to be on PATH
                            , join('fsfix', 'smoke-it.py')
                            , '--address', ':53700'
                            , '--root', join('fsfix', 'root')
                            , 'stop'
                             ])
    proc.wait()
    exc = assert_raises(IOError, urllib.urlopen, 'http://localhost:53700/')
    actual = str(exc.strerror)
    expected = "(61, 'Connection refused')"
    assert actual == expected, actual


attach_rm(globals(), 'test_')