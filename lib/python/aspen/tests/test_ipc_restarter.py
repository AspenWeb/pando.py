import errno
import logging
import os
import signal
import subprocess
import sys
import time

from aspen.ipc import restarter
from aspen.tests import LOG, Block, assert_logs
from aspen.tests.fsfix import mk, attach_teardown
from nose import SkipTest


if 'win32' == sys.platform:
    raise SkipTest # blah ... what am I doing?


ARGV = ['python', os.path.join('fsfix', 'aspen-test.py')] 
PIDFILE = os.path.join('fsfix', 'pidfile')
block = Block(PIDFILE)


# Basic
# =====

BASIC_PROGRAM = """\
from aspen.ipc import restarter
from aspen.tests import log

if restarter.PARENT:
    restarter.loop()
else:
    log.debug("done")
"""

def test_basic():
    mk(('aspen-test.py', BASIC_PROGRAM))
    subprocess.call(ARGV)
    assert_logs("done")

def test_defaults(): # dot junkie
    def assert_(foo):
        assert foo
    yield assert_, restarter.PARENT
    yield assert_, not restarter.CHILD
    yield assert_, not restarter.MONITORING
    yield assert_, restarter.EX_TEMPFAIL == 75


# Return Codes
# ============

RETCODE_TEST_PROGRAM = """\
import os
import time

from aspen.ipc import restarter
from aspen.tests import log


if restarter.PARENT:
    restarter.loop()
elif not os.path.isfile('exit'):    # restart
    log.debug("restarting")
    open('exit', 'w+').write('foo')
    raise SystemExit(%d)
else:                               # exit
    log.debug("exiting")
    os.remove('exit')
    raise SystemExit(0)

"""

def test_retcodes(): # 3 tests
    """Here are three tests against different return codes from the child.
    
    With retcode 75 we should restart immediately, but there is process
    creation fuzz. These tests are here in a generator so we can capture the
    fuzz factor from the retcode 75 case to use as a baseline for time-testing
    the retcode 1 case.

    """

    def test(retcode):
        mk(('aspen-test.py', RETCODE_TEST_PROGRAM % retcode))
        subprocess.call(ARGV)
        assert_logs("restarting", "exiting")

    start_1 = time.time()
    yield test, 75
    elapsed_1 = time.time() - start_1

    start_2 = time.time()
    yield test, 1
    elapsed_2 = time.time() - start_2

    expected = 1 # really 2 seconds, but allow for further process fuzz
    actual = elapsed_2 - elapsed_1
    def time_test():
        assert actual > expected, actual
    yield time_test


# Fixture
# =======
# This is common to both filesystem monitoring and signals testing.

RESTARTER_TEST_PROGRAM = """\
import atexit, os, signal, sys, time
from aspen.tests import log
from aspen.ipc import get_signame, restarter

import foo # will 'change' this for testing

def register_atexit(generation):
    def atexit_():
        log.debug("%s stopping" % generation)
    atexit.register(atexit_)


if restarter.PARENT:
    register_atexit('parent')
    log.debug("parent started")
    restarter.loop()

else:
    register_atexit('child')

    restarter.monitor(os.path.join('fsfix', 'foo.conf'))
    restarter.start_monitoring()

    open(os.path.join('fsfix', 'pidfile'), 'w+').write(str(os.getpid()))

    log.debug("child started")

    while 1:
        if restarter.should_restart():
            log.debug("restarting per should_restart")
            raise SystemExit(75)
        time.sleep(0.1)
"""


# Filesystem Monitoring
# =====================

def test_filesystem():
    """Changing module files or other monitored files should trigger a restart.
    """

    def test(file_to_change):
        mk( ('foo.py', '"bar"')
          , ('foo.conf', 'bar')
          , ('aspen-test.py', RESTARTER_TEST_PROGRAM)
           )
    
        proc = subprocess.Popen(ARGV) # PIPE hangs proc.communicate?
                                      #  see: http://thraxil.org/users/anders/posts/2008/03/13/Subprocess-Hanging-PIPE-is-your-enemy/
        block.start()
    
        child_pid = block.getpid()
        time.sleep(1)  # guarantee that modtime will be significantly different
        os.utime(os.path.join('fsfix', file_to_change), None) # trigger restart
        block.restart(child_pid)
    
        os.kill(proc.pid, signal.SIGINT)
        block.stop(proc.pid)
    
        assert_logs( "parent started"
                   , "child started"
                   , "restarting per should_restart"
                   , "child stopping"
                   , "child started"
                   , "parent stopping"
                   , "child stopping"
                    )
    
    yield test, 'foo.py'
    yield test, 'foo.conf'


# Signal Handling
# ===============

def _setup_signal_test():
    mk(('foo.py', ''), ('aspen-test.py', RESTARTER_TEST_PROGRAM))
    proc = subprocess.Popen(ARGV) # PIPE hangs proc.communicate?
    block.start()
    child_pid = block.getpid()
    return (proc, child_pid)


def test_sighup():
    proc, child_pid = _setup_signal_test()

    os.kill(child_pid, signal.SIGHUP)
    block.restart(child_pid)

    os.kill(proc.pid, signal.SIGINT)
    block.stop(proc.pid)

    assert_logs( "parent started"
               , "child started"
               , "child stopping"
               , "child started"
               , "parent stopping"
               , "child stopping"
                )


def test_signal():

    def test(generation, signum, expected):
        """SIGTERM/INT to parent/child should result in clean shutdown for both.
        """
        proc, child_pid = _setup_signal_test()

        if generation == 'parent':
            pid = proc.pid
        else:
            pid = child_pid

        os.kill(pid, signum)
        block.stop(child_pid)
        time.sleep(0.2) # time for log to flush
        block.stop(proc.pid)
        time.sleep(0.2) # time for log to flush
   
        assert_logs(*expected)

    expected_parent = ( "parent started"
                      , "child started"
                      , "parent stopping"
                      , "child stopping"
                       )

    expected_child = ( "parent started"
                     , "child started"
                     , "child stopping"
                     , "parent stopping"
                      )

    yield test, 'parent', signal.SIGTERM, expected_parent
    yield test, 'parent', signal.SIGINT, expected_parent
    yield test, 'child', signal.SIGTERM, expected_child
    yield test, 'child', signal.SIGINT, expected_child


###################
#
#   I'm not doing these now:
#
#   then test mixed restarting scenarios
#   also test signals w/o waiting for process to cleanly do whatever
#   THEN restarter will be solid and we can move on to daemon :^D
#
###################


attach_teardown(globals())
