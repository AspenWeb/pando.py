import StringIO
import os
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib

import aspen
from aspen.tests import NAMED_PIPE, TestTalker, hit_with_timeout
from aspen.tests import assert_actual, assert_logs, assert_raises
from aspen.tests.fsfix import mk, attach_teardown
from nose import SkipTest


ARGV = ['python', os.path.join('fsfix', 'aspen-test.py')]


PIPE_TEST_PROGRAM = """\
from aspen.tests import TestListener

listener = TestListener()
listener.listen_actively()
"""

def test_named_pipe():
    mk(('aspen-test.py', PIPE_TEST_PROGRAM))
    proc = subprocess.Popen(ARGV)
    talk = TestTalker() # blocks until FIFO is created by TestListener in proc
    talk('foo')
    talk('q')
    proc.wait()
    assert_logs("foo")


DAEMON = """\
import aspen
from aspen.tests import TestListener, configure_logging, log 
from aspen.ipc.daemon import Daemon


configuration = aspen.configure(['--root=fsfix'])
daemon = Daemon(configuration)
log.info("daemonizing, bye ...")

daemon.start() # turns us into a daemon 

configure_logging() # all fd's were closed
log.info('... daemonized, blam')

listener = TestListener()
listener.listen_actively()

"""


def test_basic():
    mk(('aspen-test.py', DAEMON))

    proc = subprocess.Popen(ARGV)

    talk = TestTalker()
    talk("Greetings, program!")
    talk('q')

    assert_logs( "daemonizing, bye ..."
               , "... daemonized, blam"
               , "Greetings, program!"
                )


def test_config_error():
    sys.stderr = stderr = StringIO.StringIO()
    try:
        exc = assert_raises(SystemExit, aspen.main, argv=['bad-command'])
    finally:
        sys.stderr = sys.__stderr__
    stderr.seek(0)

    expected = 2
    actual = exc.code
    yield assert_actual, expected, actual

    expected = ( "aspen [options] [restart,start,status,stop]; --help for more"
               , "Bad command: bad-command"
               , ""
                )
    expected = os.linesep.join(expected)
    actual = stderr.read()
    yield assert_actual, expected, actual


attach_teardown(globals())
