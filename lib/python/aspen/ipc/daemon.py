"""Daemon functionality.

Refs:

    http://code.activestate.com/recipes/278731/
    http://www.livinglogic.de/Python/daemon/
    http://blog.ianbicking.org/daemon-best-practices.html
    http://www.steve.org.uk/Reference/Unix/faq_2.html#SEC16

"""
import os
import resource
import signal
import sys
import time

from aspen.ipc import kill_nicely, log
from aspen.ipc.pidfile import ErrorState, StaleState, State
from aspen.ipc.pidfile import PIDFileMissing, PIDDead, PIDNotAspen


try:
    DEV_NULL = os.devnull
except AttributeError:
    DEV_NULL = "/dev/null"

SLEEP = 0.5


class Daemon(object):
    
    def __init__(self, configuration):
        self.configuration = configuration

    def daemonize(self):
        """Double-fork; forego a controlling terminal FOREVER.
        """

        # First fork 
        # ==========

        log.debug("first fork ...")
        pid = os.fork()
        if pid != 0:            # parent

            # Wait for pidfile to appear.
            # ===========================

            while not os.path.isfile(self.configuration.pidfile.path):
                log.debug("waiting for start ...")
                time.sleep(SLEEP)

            os._exit(0) 
        else:                   # child

            os.setsid()


            # Second fork
            # ===========
    
            log.debug("second fork ...")
            pid = os.fork()
            if pid != 0:        # parent
                os._exit(0)
            else:               # child
                os.chdir(self.configuration.paths.root)
                os.umask(0)


        # Now we're all alone in the world ...
        # ====================================
        # Time to buy our own silverware. We want new stdio streams and all
        # other file descriptors closed. The below is a combination of the 
        # approaches in Chad Schroeder's ASPN recipe and the ll.daemon module.
        # We recreate the new stdio streams first, because dup2 closes the 
        # target fd if it is open (which it is here). That way we don't have 
        # any window where we could loose our stdio streams. Then when we loop-
        # close the rest, we simply stop short of the stdio streams.
        #
        # Note that open(DEV_NULL, "r").fileno() doesn't work because the file
        # is closed once the expression is evaluated, having gone out of scope.
        # So we have to keep the two new_std* objects around until they are 
        # dup2'd. But then we want to explicitly delete those objects so that
        # we don't try to close them later (I was seeing "Bad file descriptor"
        # errors on shutdown, but that could have been because I was exiting
        # before this method returned, so the objects were still in scope(?); 
        # explicitly deleting them doesn't hurt, at least).
        #
        # And now I've gone and moved half of this into it's own method ...

        self.sighup() # reopen stdio streams

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024 

        for fd in range(maxfd, 2, -1):
            try:
                os.close(fd)
            except OSError:
                pass


    def sighup(self, signum=None, frame=None):
        """Respond to SIGHUP by reopening stdio streams.

        You would want to do this if you rotated the logfile, e.g.

        """
        new_stdin = open(DEV_NULL, "r")
        new_stdout = open(self.log_path, "a")
        fd_new_stdin = new_stdin.fileno()
        fd_new_stdout = new_stdout.fileno()

        os.dup2(fd_new_stdin,  0)   # stdin  > /dev/null
        os.dup2(fd_new_stdout, 1)   # stdout > __/var/aspen.log
        os.dup2(fd_new_stdout, 2)   # stderr > stdout

        del new_stdin
        del new_stdout


    def start(self):
        logdir = os.path.join(self.configuration.paths.root, '__', 'var')
        log_path = os.path.join(logdir, 'aspen.log')
        if not os.path.isdir(logdir):
            os.makedirs(logdir, 0755)
        self.log_path = log_path
        self.daemonize()
        signal.signal(signal.SIGHUP, self.sighup)

    def stop(self):
        child_pid = self.configuration.pidfile.getpid()
        died_nicely = kill_nicely(child_pid, is_our_child=False)
        retcode = int(not died_nicely)
        while 1:
            try:
                self.configuration.pidfile.getpid()
            except PIDFileMissing:
                break
            log.debug('waiting for stop ...')
            time.sleep(SLEEP)
        return retcode

    def restart(self):
        child_pid = self.configuration.pidfile.getpid() # raise pid errors
        new_child_pid = child_pid
        os.kill(child_pid, signal.SIGHUP)
        while new_child_pid == child_pid:
            try:
                new_child_pid = self.configuration.pidfile.getpid()
            except StaleState:
                pass
            log.debug('waiting for restart ...')
            time.sleep(SLEEP)
        return 0


    def drive(self):
        """Manipulate a daemon via a pidfile, or become one ourselves.

        Note that on principle we don't remove bad pidfiles, because they 
        indicate a bug, and are potentially useful for debugging.

        """
    
        if self.configuration.command == 'start':
            try:
                child_pid = self.configuration.pidfile.getpid()
            except PIDFileMissing:
                pass # best case
            except State, state:
                print "bad pidfile: %s" % state
                raise SystemExit(1)
            else:
                print "daemon already running with pid %d" % child_pid
                raise SystemExit(1)
            self.start()
    
        elif self.configuration.command == 'status':
            try:
                child_pid = self.configuration.pidfile.getpid()
                retcode = 0
            except PIDFileMissing:
                print "daemon not running (no pidfile)"
                retcode = 0
            except State, state:
                print state
                retcode = 1
            else:
                print "daemon running with pid %d" % child_pid
            raise SystemExit(retcode)
    
        elif self.configuration.command in ('stop', 'restart'):
            func = getattr(self, self.configuration.command)
            try:
                retcode = func()
            except State, state:
                print state
                retcode = 1 
            raise SystemExit(retcode)


        return # if command is start we'll proceed with the program
