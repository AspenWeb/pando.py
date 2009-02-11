import os

from aspen.ipc.pidfile import *
from aspen.tests.fsfix import attach_teardown, mk


class TestPIDFile(PIDFile):
    path = os.path.join('fsfix', 'pidfile')

def foo():
    """I'm seeing this crash FreeBSD 6.2-RELEASE under the test runner.

    I applied the patch from here to no avail:

        http://security.freebsd.org/advisories/FreeBSD-EN-08:01.libpthread.asc

    """
    mk(('pidfile', str(os.getpid())))
    pidfile = TestPIDFile()
    pidfile.start_monitoring()
    pidfile.stop_monitoring()

foo()

attach_teardown(globals())
