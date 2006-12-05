"""Implement a module reloading mechanism.

This module solves the problem of refreshing Python modules in memory when the
source files change, without manually restarting the program. There are two
basic ways to solve this problem:

    1. Reload modules within a single process
    -----------------------------------------

    The basic trick is to delete items from sys.modules, forcing a refresh the
    next time they are loaded. This gets tough because imported modules depend
    on each other. Look at Zope and RollbackImporter for two implementations.


    2. Maintain two processes
    -------------------------

    In this solution, a parent process continuously restarts a child process.
    This gets around module import dependencies, but the downside is that you
    loose any program state on restart, and it magnifies the shutdown/start-up
    time of your program.


This module implements the second solution. It provides the following members:

    CHILD, PARENT       These are booleans indicating whether the current
                        process is the parent or child.

    launch_child        Continuously relaunch the current program in a sub-
                        process until the exit code is something other than 75.

    should_restart      Return a boolean indicating whether the child process
                        should be restarted. If called in the parent process,
                        it always returns False.


Our implementation uses a thread in the child process (started when the module
is imported) to monitor all library source files. Your program is responsible
for periodically calling mods_changed, exiting with code 75 whenever it returns
True (presumably after cleanly shutting down). Exit code 75 seemed appropriate
to use because of its meaning on Unix systems:

    EX_TEMPFAIL -- temporary failure, indicating something that
    *              is not really an error.  In sendmail, this means
    *              that a mailer (e.g.) could not create a connection,
    *              and the request should be reattempted later.
    [...]
    #define EX_TEMPFAIL     75      /* temp failure; user is invited to retry */

    -- /usr/include/sysexits.h, FreeBSD 6.1-RELEASE


Here's an example of what this looks like:

    import restarter

    def main():
        while 1:
            # program logic here
            if restarter.should_restart():
                # shutdown code here
                raise SystemExit(75)

    if restarter.PARENT:
        restarter.launch_child()
    else:
        main()


This module requires the subprocess module. Included in the standard library
since Python 2.4, it can also be found here:

    http://www.lysator.liu.se/~astrand/popen5/

"""
__author__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "custom" # patch submitted as lib537 issue #1


import os
import sys
import threading
import time

try:
    import subprocess
    _HAVE_SUBPROCESS = True
except ImportError:
    _HAVE_SUBPROCESS = False


_FLAG = '_RESTARTER_CHILD_FLAG'
CHILD = _FLAG in os.environ
PARENT = not CHILD
EX_TEMPFAIL = 75


def _look_for_changes():
    """See if any of our available modules have changed on the filesystem.
    """

    mtimes = {}
    while 1:
        for module in sys.modules.values():

            # Get out early if we can.
            # ========================

            filename = getattr(module, '__file__', None)
            if filename is None:
                continue
            if filename.endswith(".pyc"):
                filename = filename[:-1]


            # The file may have been removed from the filesystem.
            # ===================================================

            if not os.path.isfile(filename):
                if filename in mtimes:
                    return # trigger restart


            # Or not, in which case, check the mod time.
            # ==========================================

            mtime = os.stat(filename).st_mtime
            if filename not in mtimes: # first time we've seen it
                mtimes[filename] = mtime
                continue
            if mtime > mtimes[filename]:
                return # trigger restart

        time.sleep(0.1)


if CHILD:
    _thread = threading.Thread(target=_look_for_changes)
    _thread.setDaemon(True)
    _thread.start()


# Public functions
# ================

def launch_child():
    """Keep relaunching the child until it exits 0.
    """
    if not _HAVE_SUBPROCESS:
        raise NotImplementedError("You do not have the subprocess module.")
    elif CHILD:
        raise NotImplementedError("We *are* the child.")

    args = [sys.executable] + sys.argv
    new_env = os.environ.copy()
    new_env[_FLAG] = 'foo'
    while 1:
        retcode = subprocess.call(args, env=new_env)
        if retcode == 75:   # child wants restart
            continue
        elif retcode > 0:   # child erred; block until mods changed
            _look_for_changes()
        else:               # child exited successfully; propagate
            raise SystemExit


def should_restart():
    if PARENT:
        return False
    else:
        return not _thread.isAlive()


# Test
# ====

if __name__ == '__main__':
    """Simple test.

    Execute this module as a script, then change the value of bar in foo.py. You
    should see 'restarting ...'  and then the new value of foo.bar.

    """

    if PARENT and os.path.isfile('foo.py'):
        print 'test aborted: foo.py exists'
        raise SystemExit

    def main():
        import foo
        print foo.bar
        while 1:
            time.sleep(1)
            if should_restart():
                print "restarting ..."
                raise SystemExit(75)

    try:
        if PARENT:
            open('foo.py', 'w+').write("bar='Blah.'")
            launch_child()
        else:
            main()

    finally:
        if PARENT:
            os.remove('foo.py')
            os.remove('foo.pyc')


# Legal
# =====

"""
This module is based on work by Ian Bicking and the CherryPy team:

    http://svn.cherrypy.org/tags/cherrypy-2.2.1/cherrypy/lib/autoreload.py


Their work is used under the MIT and/or new BSD licenses. All new work is:

    Copyright (c) 2006 Chad Whitacre <chad@zetaweb.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to
    deal in the Software without restriction, including without limitation the
    rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
    sell copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
    IN THE SOFTWARE.

    <http://opensource.org/licenses/mit-license.php>

"""