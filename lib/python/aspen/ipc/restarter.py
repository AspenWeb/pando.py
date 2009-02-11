"""Automatically restart a program on SystemExit or when certain files.

This module solves the problem of refreshing modules in memory when the source
files change. There are two basic ways to solve this problem:

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


This module implements the second solution, automatically watching source files
for all loaded modules (with the exception of those imported directly from a
ZIP archive via zipimport). Employing a process boundary means this module can
also be used for server thrashing. We can also watch non-source files, such as
configuration files. This module provides the following members:

    CHILD, PARENT       These are booleans indicating whether the current
                        process is the parent or child.

    loop                Continuously relaunch the current program in a sub-
                        process until the exit code is something other than 75.

    should_restart      Return a boolean indicating whether the child process
                        should be restarted. If called in the parent process,
                        it always returns False. If you don't call monitor_
                        filesystem first, it always returns True.

    watch(filepath)     Add <filepath> to the list of non-source files to watch.
                        If the file is removed or has its modtime changed, the
                        program will restart.

    monitor_filesystem()  Turn on a thread that monitors filesystem activity,
                        restarting the server if watched files or module files
                        change.


Our implementation uses a thread in the child process to monitor all library
source files as well as those added with watch. Your program is responsible for
periodically calling should_restart, exiting with code 75 whenever it returns
True (presumably after cleanly shutting down). Exit code 75 seems appropriate
because of its meaning on Unix systems.  E.g., from FreeBSD 6.1-RELEASE,
/usr/include/sysexits.h:

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
        restarter.watch('foo.conf') # your conf file; change to trigger
                                    # reloading
        while 1:
            # program logic here
            if restarter.should_restart():
                # shutdown code here
                print "restarting ..."
                raise SystemExit(75)

    if restarter.PARENT:
        restarter.loop()
    else:
        restarter.monitor_filesystem()
        main()


This module requires the subprocess module. Included in the standard library
since Python 2.4, it can also be found here:

    http://www.lysator.liu.se/~astrand/popen5/

"""
__author__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "~~VERSION~~"


import atexit
import errno
import os
import signal
import sys
import threading
import time

from aspen.ipc import kill_nicely, log, get_signame


try:
    import subprocess
    _HAVE_SUBPROCESS = True
except ImportError:
    _HAVE_SUBPROCESS = False


_FILES = []                         # non-module files to monitor 
_FLAG = '_RESTARTER_CHILD_FLAG'     # flag for tracking child/parent process
CHILD = _FLAG in os.environ         # True w/in child process
PARENT = not CHILD                  # True w/in parent process
EX_TEMPFAIL = 75                    # child's exit code to trigger restart
MONITORING = False                  # whether we are monitoring the filesystem
child = None                        # our only child
CAUGHT_SIGHUP = False               # flag that we caught a SIGHUP signal
SIGNAL = None                       # the signal we are handling; pass to child


# Signal handling
# ===============

if CHILD:
    def sighup(signum, frame):
        global SIGNAL
        if SIGNAL is None: # only shutdown once
            SIGNAL = signum
            log.debug("sighup_child: restarting")
            raise SystemExit(75) # trigger restart w/ atexit
    signal.signal(signal.SIGHUP, sighup)


def terminate(signum, frame):
    """Shutdown both parent and child cleanly.
    """
    global SIGNAL
    if SIGNAL is None: # only shutdown once (if we are already exiting 75 on 
                       # SIGHUP then presumably our parent won't restart us) 
        SIGNAL = signum
        generation = PARENT and 'parent' or 'child'
        log.debug("exiting %s on %s" % (generation, get_signame(signum)))
        raise SystemExit(0) # (debugging hint: was the previous call blocking?)

signal.signal(signal.SIGINT, terminate)
signal.signal(signal.SIGTERM, terminate)


# atexit
# ======

def cleanup_parent():
    global child
    log.debug("cleaning up restarter in parent")
    if child is not None:
        kill_nicely(child.pid, is_our_child=True)
        child = None    # explicitly trigger destructor to avoid stderr spam
        time.sleep(1)   # give stdout a chance to settle (child to terminate?)

def cleanup_child():
    log.debug("cleaning up restarter in child")
    if MONITORING:
        stop_monitoring()

cleanup = PARENT and cleanup_parent or cleanup_child
atexit.register(cleanup)


# Define thread 
# =============

_monitor = None # this is our thread; set in _initialize() below

def _monitor_filesystem():
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


    while not _monitor.stop.isSet():
        for module in sys.modules.values():                 # module files
            filepath = getattr(module, '__file__', None)
            if filepath is None:
                continue # @@: really just ignore this? when would this happen?
            filepath = filepath.endswith(".pyc") and filepath[:-1] or filepath
            if has_changed(filepath):
                return # triggers restart

        for filepath in _FILES:                             # additional files
            if has_changed(filepath):
                return # triggers restart

        time.sleep(0.1)


def _initialize():
    """Initialize the _monitor thread; factored out for testing.

    Threads can only be started once, they can't be joined and then restarted,
    so we have to recreate the _monitor thread in between tests. The
    alternative is to make a class a la PIDFile, but signal handling precludes
    that. Signal handling is process-global, so this functionality also needs
    to be process-global (hence, module level).

    """
    global _monitor
    _monitor = threading.Thread(target=_monitor_filesystem)
    _monitor.stop = threading.Event()
    _monitor.setDaemon(True) # don't prevent program from exiting
    _monitor.setName("Restarter")

_initialize()


# Public functions
# ================

def loop(argv=None):
    """Keep relaunching the child until it exits 0.

    Use return code 75 to trigger an immediate restart. Other non-zero return
    codes will have a two-second throttle. SIGHUP also restarts (in either 
    parent or child).

    """
    global child 

    if not _HAVE_SUBPROCESS:
        raise NotImplementedError("You do not have the subprocess module. See "
                                  "http://www.lysator.liu.se/~astrand/popen5/")
    elif CHILD:
        raise NotImplementedError("We *are* the child.")


    if argv is None: # only True in testing
        argv = sys.argv
    args = [sys.executable] + argv
    log.debug("entering restarter loop with %s" % args)
    new_env = os.environ.copy()
    new_env[_FLAG] = 'foo'
    while 1:

        # Start the child and get a return code.
        # ======================================
        # For the record, this was a whole lot more complicated when we were
        # capturing SIGHUP in the parent and passing it on to the child, 
        # because it would interrupt the os.wait call inside child.wait, but
        # so would SIGTERM/SIGINT, so we had to keep track of which signal
        # we were handling and re-call child.wait if it was SIGHUP. Anyway,
        # we don't have to do that anymore. When PARENT is a daemon, SIGHUP 
        # is used for reopening stdio streams (see ipc/daemon.py); otherwise
        # it's a clean shutdown just like SIGTERM/SIGINT.
        
        log.debug("launching child from %d" % os.getpid())
        child = subprocess.Popen(args, env=new_env)
        retcode = child.wait()
        log.debug("child (%d) returned %d" % (child.pid, retcode))


        # Process the return code.
        # ========================

        if retcode == 0:    # child exited successfully; propagate
            raise SystemExit(0)
        elif retcode == 75: # child wants immediate restart
            continue 
        else:               # child erred; thrash until otherwise
            time.sleep(2)   #  (this is terrible parenting, by the way ...)


def should_restart():
    """Return a boolean; True means "Please restart me."
    """
    if PARENT:
        return False
    elif MONITORING:
        return not _monitor.isAlive()
    else:
        return False # if not file-monitoring, will only restart on SystemExit


def monitor(filepath):
    """Add filepath to the list of files to restart onchange.
    """
    _FILES.append(filepath)

track = monitor # backwards-compatibility


def start_monitoring():
    """Turn on filesytem monitoring.
    """
    global MONITORING
    MONITORING = True
    _monitor.start()


def stop_monitoring():
    """Turn off filesystem monitoring.
    
    It is a bug to call this without having called start_monitoring first.

    """
    global MONITORING
    MONITORING = False
    _monitor.stop.set()
    _monitor.join()
    _initialize()


# Legal
# =====

"""
This module is based on work by Ian Bicking and the CherryPy team:

    http://svn.cherrypy.org/tags/cherrypy-2.2.1/cherrypy/lib/autoreload.py


Their work is used under the MIT and/or new BSD licenses. All new work is:

    Copyright (c) 2006-2009 Chad Whitacre <chad@zetaweb.com>

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
