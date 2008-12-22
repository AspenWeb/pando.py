import os
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib
from os.path import join, isfile

from aspen.tests import BIN_ASPEN, assert_raises
from aspen.tests.fsfix import mk, attach_rm


# Another top-level test
# ======================

def test_daemon():
    if 'win' in sys.platform:
        return # don't bother running this test on Windows

    mk( 'root', 'root/__', ('root/index.html', "Greetings, program!")
      , ('smoke-it.py', BIN_ASPEN) # simulate bin/aspen
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


def test_pidfile_waxed_when_address_in_use():
    if 'win' in sys.platform:
        return # don't bother running this test on Windows

    mk( 'root', 'root/__', ('root/index.html', "Greetings, program!")
      , ('smoke-it.py', BIN_ASPEN) # simulate bin/aspen
       )


    # Steal the socket.
    # =================

    sock = socket.socket()
    sock.bind(('0.0.0.0', 53701))


    # Start the daemon.
    # =================

    proc2 = subprocess.Popen([ 'python' # assumed to be on PATH
                            , join('fsfix', 'smoke-it.py')
                            , '--address', '0.0.0.0:53701'
                            , '--root', join('fsfix', 'root')
                            , 'start'
                             ])
    time.sleep(1) # give it time to start up


    # Check pidfile.
    # ==============
    # We have to wait for the daemon to crash; give it a 5-second timeout.

    then = time.time()
    TIMEOUT = 5
    while 1:
        there = isfile('fsfix/root/__/var/aspen.pid')
        if (not there) or (time.time() > then + TIMEOUT):
            break
        time.sleep(0.2)
    actual = there
    expected = False
    assert actual == expected, actual


attach_rm(globals(), 'test_')
