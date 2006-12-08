"""Define the main program loop.
"""
import base64
import logging
import os
import signal
import sys
import threading
import time
from optparse import OptionError
from os.path import isdir, isfile, join

from aspen import mode, restarter
from aspen.daemon import Daemon
from aspen.server import CherryPyWSGIServer as Server
from aspen.config import ConfigError, Configuration, usage


__version__ = '~~VERSION~~'


log = logging.getLogger('aspen')
KILL_TIMEOUT = 5 # number of seconds between shutdown attempts


class PIDFiler(threading.Thread):
    """Thread to continuously monitor a pidfile, keeping our pid in the file.

    This is run when we are a daemon, in the child process.

    """

    stop = threading.Event()
    path = '' # path to the pidfile

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """Pidfile is initially created and finally destroyed by our Daemon.
        """
        while not self.stop.isSet():
            if not isfile(self.path):
                print "no pidfile; recreating"
                open(self.path, 'w+').write(str(os.getpid()))
            time.sleep(0.1)
        if isfile(self.path): # sometimes we beat handlesigterm
            os.remove(self.path)

pidfiler = PIDFiler() # must actually set pidfiler.path before starting


def start_server(config):
    """The heavy work of instantiating and starting a website.
    """

    # Delayed import.
    # ===============
    # @@: does this really help w/ boot up time in restart mode?

    from aspen.website import Website


    # Build the website and server.
    # =============================

    config.load_plugins()
    website = Website(config)
    for app in config.middleware:
        website = app(website)
    server = Server(config.address, website)


    # Monkey-patch server to support restarting.
    # ==========================================
    # Giving server a chance to shutdown cleanly avoids the terminal screw-up
    # bug that plagued httpy < 1.0.

    if restarter.CHILD:
        def tick():
            Server.tick(server)
            if restarter.should_restart():
                print >> sys.stderr, "restarting ..."
                server.stop()
                raise SystemExit(75)
        server.tick = tick


    # Loop.
    # =====

    try:
        print "aspen starting on %s" % str(config.address)
        #log.info("aspen starting on %s" % str(config.address))
        server.start()
    finally:
        print "stopping server"
        server.stop()
        if pidfiler.isAlive(): # we're a daemon
            pidfiler.stop.set()
            pidfiler.join()


def drive_daemon(config):
    """Manipulate a daemon.
    """

    __ = join(config.paths.root, '__')
    if isdir(__):
        var = join(__, 'var')
        if not isdir(var):
            os.mkdir(var)
        pidfile = join(var, 'aspen.pid')
        logpath = join(var, 'aspen.log')
    else:
        key = base64.urlsafe_b64encode(config.paths.root)
        pidfile = os.sep + join('tmp', 'aspen-%s.pid' % key)
        logpath = '/dev/null'

    daemon = Daemon(stdout=logpath, stderr=logpath, pidfile=pidfile)


    # Start/stop wrappers
    # ===================

    def start():
        print "starting daemon"
        daemon.start()
        pidfiler.path = pidfile
        pidfiler.start()
        start_server(config)


    def stop():

        # Get the pid.
        # ============

        if not isfile(pidfile):
            print "daemon not running"
            raise SystemExit(1)
        data = open(pidfile).read()
        try:
            pid = int(data)
        except ValueError:
            print "mangled pidfile %s: %r" % (pidfile, data)
            raise SystemExit(1)


        # Try pretty hard to kill the process nicely.
        # ===========================================

        def kill(sig):
            try:
                os.kill(pid, sig)
            except OSError, exc:
                print str(exc)
                raise SystemExit(1)

        nattempts = 0
        while isfile(pidfile):

            if nattempts == 0:
                kill(signal.SIGTERM)

            elif nattempts == 1:
                print "still going; resending SIGTERM"
                kill(signal.SIGTERM)

            elif nattempts == 2:
                print "STILL going; sending SIGKILL to %d and quiting" % pid
                kill(signal.SIGKILL)
                raise SystemExit(1)


            nattempts += 1
            last_attempt = time.time()
            while 1:
                if not isfile(pidfile):
                    print 'stopped'
                    return
                elif (last_attempt + KILL_TIMEOUT) < time.time():
                    break
                else:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    time.sleep(0.2)


    # Branch
    # ======

    if config.command == 'start':
        if isfile(pidfile):
            print "pidfile already exists with pid %s" % open(pidfile).read()
            raise SystemExit(1)
        start()

    elif config.command == 'stop':
        stop()
        raise SystemExit(0)

    elif config.command == 'restart':
        stop()
        start()


def main(argv=None):
    """Initial phase of config parsing, and daemon/restarter/server branch.
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        config = Configuration(argv)
    except ConfigError, err:
        print >> sys.stderr, usage
        print >> sys.stderr, err.msg
        raise SystemExit(2)

    try:
        if config.daemon:
            drive_daemon(config)
        elif mode.DEBDEV and restarter.PARENT:
            restarter.launch_child()
        else:
            start_server(config)
    except KeyboardInterrupt:
        pass
