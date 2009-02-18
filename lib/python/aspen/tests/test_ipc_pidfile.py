import os
import stat
import sys

from aspen.ipc.pidfile import *
from aspen.tests import assert_logs, assert_raises, set_log_filter
from aspen.tests.fsfix import attach_teardown, mk
from nose import SkipTest


if 'win32' == sys.platform:
    raise SkipTest # PIDFile object is created on windows but never written


class TestPIDFile(PIDFile):
    def __init__(self):
        PIDFile.__init__(self, os.path.join('fsfix', 'pidfile'))


def test_basic():
    pid = os.getpid()
    mk(('pidfile', str(pid)))
    pidfile = TestPIDFile()
    actual = pidfile.getpid()
    expected  = pid
    assert actual == expected, actual


# Basic Management
# ================

def test_write():
    mk()
    pidfile = TestPIDFile()
    pidfile.write()
    actual = os.path.isfile(pidfile.path)
    expected = True
    assert actual == expected, actual

def test_write_writes_it():
    mk()
    pidfile = TestPIDFile()
    pidfile.write()
    actual = int(open(pidfile.path).read())
    expected = os.getpid()
    assert actual == expected, actual

def test_write_sets_perms():
    mk()
    pidfile = TestPIDFile()
    pidfile.write()
    actual = os.stat(pidfile.path)[stat.ST_MODE] & 0777
    expected = pidfile.mode 
    assert actual == expected, actual

def test_write_creates_directory():
    mk()
    nested = os.path.join('fsfix', '__', 'var', 'pidfile')
    pidfile = TestPIDFile()
    pidfile.path = nested
    pidfile.write()
    actual = os.path.isfile(nested)
    expected = True
    assert actual == expected, actual

def test_write_sets_directory_perms():
    mk()
    nested = os.path.join('fsfix', '__', 'var', 'pidfile')
    pidfile = TestPIDFile()
    pidfile.path = nested
    pidfile.write()
    actual = os.stat(os.path.dirname(pidfile.path))[stat.ST_MODE] & 0777
    expected = pidfile.dirmode 
    assert actual == expected, actual


def test_setperms(): # yes, this is a cheap dot
    pidfile = TestPIDFile()
    mk(('pidfile', 'foo'))
    pidfile.setperms()
    actual = os.stat(pidfile.path)[stat.ST_MODE] & 0777
    expected = pidfile.mode
    assert actual == expected, actual


def test_remove():
    mk()
    pidfile = TestPIDFile()
    pidfile.write()
    pidfile.remove()
    actual = os.path.isfile(pidfile.path)
    expected = False
    assert actual == expected, actual


# Get PID
# =======

def test_getpid(): # another cheap dot :^)
    pid = os.getpid()
    mk(('pidfile', str(pid)))
    pidfile = TestPIDFile()
    actual = pidfile.getpid()
    expected  = pid
    assert actual == expected, actual

def test_getpid_path_not_set():
    pidfile = TestPIDFile()
    pidfile.path = None
    assert_raises(PIDFilePathNotSet, pidfile.getpid)

def test_getpid_missing():
    for exc in (PIDFileMissing, StaleState):
        pidfile = TestPIDFile()
        yield assert_raises, exc, pidfile.getpid

def test_getpid_restricted():
    for exc in (PIDFileRestricted, ErrorState):
        mk(('pidfile', str(os.getpid())))
        pidfile = TestPIDFile()
        os.chmod(pidfile.path, 0000)
        yield assert_raises, exc, pidfile.getpid


def test_getpid_empty():
    for exc in (PIDFileEmpty, ErrorState):
        mk(('pidfile', ''))
        pidfile = TestPIDFile()
        yield assert_raises, exc, pidfile.getpid

def test_getpid_mangled():
    for exc in (PIDFileMangled, ErrorState):
        mk(('pidfile', 'foo'))
        pidfile = TestPIDFile()
        yield assert_raises, exc, pidfile.getpid

def test_getpid_mangled_newline():
    for exc in (PIDFileMangled, ErrorState):
        mk(('pidfile', str(os.getpid)+'\n'))
        pidfile = TestPIDFile()
        yield assert_raises, exc, pidfile.getpid


def test_getpid_dead():
    for exc in (PIDDead, StaleState):
        mk(('pidfile', '99999')) # yes, this could fail
        pidfile = TestPIDFile()
        yield assert_raises, exc, pidfile.getpid

def test_getpid_not_aspen():
    for exc in (PIDNotAspen, StaleState):
        pid = os.getpid()
        mk(('pidfile', str(pid)))
        pidfile = TestPIDFile()
        pidfile.ASPEN = 'flahflah'
        yield assert_raises, exc, pidfile.getpid


attach_teardown(globals())
