"""Automatically restart your program when certain files change.

This module primarily solves the problem of refreshing modules in memory when
the source files change. There are two basic ways to solve this problem:

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


This module implements the second solution, automatically tracking source files
for all loaded modules, with the exception of those imported directly from a ZIP
archive (via zipimport). This module can also track non-source files, such as
configuration files. It provides the following members:

    CHILD, PARENT       These are booleans indicating whether the current
                        process is the parent or child.

    launch_child        Continuously relaunch the current program in a sub-
                        process until the exit code is something other than 75.

    should_restart      Return a boolean indicating whether the child process
                        should be restarted. If called in the parent process,
                        it always returns False.

    track(filepath)     Add <filepath> to the list of non-source files to track.
                        If the file is removed or has its modtime changed, the
                        program will restart.


Our implementation uses a thread in the child process (started when the module
is imported) to monitor all library source files as well as those added with
track. Your program is responsible for periodically calling should_restart,
exiting with code 75 whenever it returns True (presumably after cleanly shutting
down). Exit code 75 seems appropriate because of its meaning on Unix systems.
E.g., from FreeBSD 6.1-RELEASE, /usr/include/sysexits.h:

    EX_TEMPFAIL -- temporary failure, indicating something that
    *              is not really an error.  In sendmail, this means
    *              that a mailer (e.g.) could not create a connection,
    *              and the request should be reattempted later.
    [...]
    #define EX_TEMPFAIL     75      /* temp failure; user is invited to retry */

    -- /usr/include/sysexits.h, FreeBSD 6.1-RELEASE


A modified file dependency is "not really an error," and the parent process is
"invited to retry" launching the child program.

Here's an example of what this looks like:

    import restarter
    import foo # your module; change to trigger reloading

    def main():
        # startup code here
        restarter.track('foo.conf') # your conf file; change to trigger
                                    # reloading
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
__version__ = "~~VERSION~~"


import os
import sys
import threading
import time

try:
    import subprocess
    _HAVE_SUBPROCESS = True
except ImportError:
    _HAVE_SUBPROCESS = False


_FILES = []                         # non-module files to track
_FLAG = '_RESTARTER_CHILD_FLAG'     # flag for tracking child/parent process
CHILD = _FLAG in os.environ         # True w/in child process
PARENT = not CHILD                  # True w/in parent process
EX_TEMPFAIL = 75                    # child's exit code to trigger restart


def _look_for_changes():
    """See if any of our available modules have changed on the filesystem.

    This function is run as a daemon thread. When this function returns, the
    thread dies, and that is the signal to restart the process.

    """

    mtimes = {}

    def has_changed(filename):
        """Given a filename, return True or False.
        """

        # The file may have been removed from the filesystem.
        # ===================================================

        if not os.path.isfile(filename):
            if filename in mtimes:
                return True # trigger restart
            else:
                # We haven't seen the file before. It has been probably
                # loaded from a zip (egg) archive.
                return False


        # Or not, in which case, check the mod time.
        # ==========================================

        mtime = os.stat(filename).st_mtime
        if filename not in mtimes: # first time we've seen it
            mtimes[filename] = mtime
        if mtime > mtimes[filename]:
            return True # trigger restart


        return False


    while 1:
        for module in sys.modules.values():                 # module files
            filepath = getattr(module, '__file__', None)
            if filepath is None:
                continue
            filepath = filepath.endswith(".pyc") and filepath[:-1] or filepath
            if has_changed(filepath):
                return # triggers restart

        for filepath in _FILES:                             # additional files
            if has_changed(filepath):
                return # triggers restart

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
        elif retcode > 0:   # child erred; thrash until otherwise
            time.sleep(2)
        else:               # child exited successfully; propagate
            raise SystemExit


def should_restart():
    if PARENT:
        return False
    else:
        return not _thread.isAlive()


def track(filepath):
    _FILES.append(filepath)


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
