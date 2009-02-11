import os
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib

import aspen
from aspen._configuration import Configuration
from aspen.exceptions import *
from aspen.tests import Block, assert_, assert_actual, assert_raises
from aspen.tests import hit_with_timeout
from aspen.tests.fsfix import mk, attach_teardown
from aspen.website import Website as _Website


# Fixture
# =======

class DummyServer:
    pass

def Website():
    config = Configuration(['--root=fsfix'])
    config.load_plugins()
    server = DummyServer()
    server.configuration = config
    return _Website(server)

class Aspen(Block):
    """Encapsulate a running aspen server.
    """

    def __init__(self):
        proc = subprocess.Popen( [ 'aspen' # assumed to be on PATH
                                 , '--address=:53700'
                                 , '--root=fsfix'
                                 , '--mode=production'
                                 , '--log-level=NIRVANA'
                                  ]
                                )
        self.proc = proc

    def getpid(self):
        return self.proc.pid

    def hit_and_terminate(self, path='/'):
        url = "http://localhost:53700" + path
        output = hit_with_timeout(url)
        kill(self.proc.pid, signal.SIGTERM)
        self.stop(self.proc.pid)
        return output


# Define a cross-platform kill().
# ===============================
# http://python.org/infogami-faq/windows/how-do-i-emulate-os-kill-in-windows/

if 'win' in sys.platform:
    # @@: in 2.6 os.kill works on windows
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
    mk(('index.html', "Greetings, program!"))
    aspen = Aspen()
    expected = "Greetings, program!"
    actual = aspen.hit_and_terminate()
    assert actual == expected, actual


def test_your_first_handler():

    def setup():
        mk( ('__/lib/python/handy.py', """\
def handle(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [environ['PATH_TRANSLATED']]
    """)
          , ('__/etc/handlers.conf', """\
fnmatch aspen.rules:fnmatch

[handy:handle]
fnmatch *.asp
    """)
          , ('handled.asp', "Greetings, program?")
            )

    PATH_TRANSLATED = os.path.realpath(os.path.join('fsfix', 'handled.asp'))


    # Hit it from the inside.
    # =======================

    setup()
    expected = [PATH_TRANSLATED]
    actual = Website()({'PATH_INFO':'handled.asp'}, lambda a,b:a)
    yield assert_actual, expected, actual


    # Then hit it from the outside.
    # =============================

    setup()
    expected = PATH_TRANSLATED
    aspen = Aspen()
    actual = aspen.hit_and_terminate('/handled.asp')
    yield assert_actual, expected, actual


def test_auto_index():
    mk('FOO', '__')
    aspen = Aspen()
    actual = aspen.hit_and_terminate()
    yield assert_, 'FOO' in actual
    yield assert_, '__' not in actual


attach_teardown(globals())
