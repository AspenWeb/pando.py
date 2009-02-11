"""Top level tests; see also test_tutorial and test_daemon.
"""
import os
import socket
import time
from subprocess import Popen, PIPE, STDOUT

import aspen
from aspen.server import Server
from aspen.tests import LOG, hit_with_timeout
from aspen.tests import assert_, assert_actual, assert_logs, assert_raises
from aspen.tests.fsfix import mk, attach_teardown


ARGV = ['aspen']


# Fixture
# =======

PIDPATH = os.path.join('fsfix', '__', 'var', 'aspen.pid')
def getpid(): # for our use of this in these test, missing PIDPATH is a bug
    return open(PIDPATH).read()

def daemon_cmd(cmd):
    fp = open(LOG, 'a')
    argv = ['aspen', '--root=fsfix', '--address=:53700', cmd]
    proc = Popen(argv, stdout=fp, stderr=STDOUT)
    proc.wait()

def with_daemon(func):
    daemon_cmd('start')
    try:
        func()
    finally:
        daemon_cmd('stop')


# Tests
# =====

def test_daemon():
    mk() 
    daemon_cmd('start')
    daemon_cmd('stop')
    assert_logs(None)

def test_daemon_restart():
    mk() 
    daemon_cmd('start')
    daemon_cmd('restart')
    daemon_cmd('stop')
    assert_logs(None)

def test_daemon_status():
    mk() 
    daemon_cmd('start')
    pid = getpid()
    daemon_cmd('status')
    daemon_cmd('stop')
    assert_logs('daemon running with pid %s' % pid)

def test_daemon_start_twice():
    mk() 
    daemon_cmd('start')
    pid = getpid()
    daemon_cmd('start')
    daemon_cmd('stop')
    assert_logs('daemon already running with pid %s' % pid)

def test_daemon_stop_not_running():
    mk() 
    daemon_cmd('stop')
    assert_logs('pidfile ./fsfix/__/var/aspen.pid is missing (is aspen '
                'running?)')

def test_daemon_restart_not_running():
    mk() 
    daemon_cmd('restart')
    assert_logs('pidfile ./fsfix/__/var/aspen.pid is missing (is aspen '
                'running?)')

def test_daemon_status_not_running():
    mk() 
    daemon_cmd('status')
    assert_logs('daemon not running (no pidfile)')
    
def test_daemon_creates_var_dir():
    mk() 
    daemon_cmd('start')
    daemon_cmd('stop')
    assert os.path.isdir(os.path.join('fsfix', '__', 'var'))


def test_aspen_hit_it():
    mk(('index.html', 'Greetings, program!'))
    def test():
        expected = 'Greetings, program!'
        actual = hit_with_timeout('http://localhost:53700/')
        assert actual == expected, actual
    with_daemon(test)


def test_conflicting_address():
    def test():
        configuration = aspen.configure(['--address=:53700'])
        server = Server(configuration)
        yield assert_raises, socket.error, server.start
    with_daemon(test)

attach_teardown(globals())
