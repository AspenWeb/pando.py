"""Define the main program loop.
"""
import base64
import os
import signal
import sys
import threading
import time
from optparse import OptionError
from os.path import isdir, isfile, join

from aspen import mode, restarter
from aspen.wsgiserver import CherryPyWSGIServer as Server
from aspen.config import ConfigError, Configuration, usage

try:
    from aspen.daemon import Daemon
except ImportError:
    Daemon = None # windows; aspen.daemon requires pwd


__version__ = '~~VERSION~~'


KILL_TIMEOUT = 5 # seconds between shutdown attempts
PIDCHECK_TIMEOUT = 60 # seconds between pidfile writes

class PIDFiler(threading.Thread):
    """Thread to continuously monitor a pidfile, keeping our pid in the file.

    This is run when we are a daemon, in the child process. It checks every
    second to see if the file exists, recreating it if not. It also rewrites the
    file every 60 seconds, in case the contents have changed.

    """

    stop = threading.Event()
    path = '' # path to the pidfile

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def write(self):
        open(self.path, 'w+').write(str(os.getpid()))

    def run(self):
        """Pidfile is initially created and finally destroyed by our Daemon.
        """
        last_pidcheck = 0
        while not self.stop.isSet():
            if not isfile(self.path):
                print "no pidfile; recreating"
                sys.stdout.flush()
                self.write()
            elif (last_pidcheck + PIDCHECK_TIMEOUT) < time.time():
                self.write()
                last_pidcheck = time.time()
            time.sleep(1)
        if isfile(self.path): # sometimes we beat handlesigterm
            os.remove(self.path)

pidfiler = PIDFiler() # must actually set pidfiler.path before starting


def start_server(config):
    """This is the heavy work of instantiating and starting a website.
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
    server = Server(config.address, website, 10, 'Aspen/%s' % __version__)


    # Monkey-patch server to support restarting.
    # ==========================================
    # Giving server a chance to shutdown cleanly avoids the terminal screw-up
    # bug that plagued httpy < 1.0.

    if restarter.CHILD:
        def tick():
            Server.tick(server)
            if restarter.should_restart():
                print "restarting ..."
                server.stop()
                raise SystemExit(75)
        server.tick = tick


    # Loop.
    # =====

    try:
        print "aspen starting on %s" % str(config.address)
        sys.stdout.flush()
        server.start()
    finally:
        print "stopping server"
        sys.stdout.flush()
        server.stop()
        if pidfiler.isAlive(): # we're a daemon
            pidfiler.stop.set()
            pidfiler.join()


def drive_daemon(config):
    """Manipulate a daemon or become one ourselves.
    """

    # Locate some paths.
    # ==================

    __ = join(config.paths.root, '__')
    if isdir(__):
        var = join(__, 'var')
        if not isdir(var):
            os.mkdir(var)
        pidfile = join(var, 'aspen.pid')
        logpath = join(var, 'aspen.log')
    else:
        key = ' '.join([str(config.address), config.paths.root])
        key = base64.urlsafe_b64encode(key)
        pidfile = os.sep + join('tmp', 'aspen-%s.pid' % key)
        logpath = '/dev/null'


    # Instantiate the daemon.
    # =======================

    daemon = Daemon(stdout=logpath, stderr=logpath, pidfile=pidfile)


    # Start/stop wrappers
    # ===================

    def start():
        daemon.start()
        pidfiler.path = pidfile
        pidfiler.start()
        start_server(config)


    def stop(stop_output=True):

        # Get the pid.
        # ============

        if not isfile(pidfile):
            print "daemon not running"
            raise SystemExit(1)
        data = open(pidfile).read()
        try:
            pid = int(data)
        except ValueError:
            print "mangled pidfile: '%r'" % data
            raise SystemExit(1)


        # Try pretty hard to kill the process nicely.
        # ===========================================
        # We send two SIGTERMs and a SIGKILL before quitting. The daemon gets
        # 5 seconds after each to shut down.

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
                print "%d still going; resending SIGTERM" % pid
                kill(signal.SIGTERM)
            elif nattempts == 2:
                print "%d STILL going; sending SIGKILL and quiting" % pid
                kill(signal.SIGKILL)
                raise SystemExit(1)
            nattempts += 1

            last_attempt = time.time()
            while 1:
                if not isfile(pidfile):
                    return # daemon has stopped
                elif (last_attempt + KILL_TIMEOUT) < time.time():
                    break # daemon hasn't stopped; time to escalate
                else:
                    time.sleep(0.2)


    # Branch
    # ======

    if config.command == 'start':
        if isfile(pidfile):
            print "pidfile already exists with pid %s" % open(pidfile).read()
            raise SystemExit(1)
        start()

    elif config.command == 'status':
        if isfile(pidfile):
            pid = int(open(pidfile).read())
            command = "ps auxww|grep ' %d .*aspen'|grep -v grep" % pid
            # @@: I doubt this command is portable.
            os.system(command)
            raise SystemExit(0)
        else:
            print "daemon not running"
            raise SystemExit(0)

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
        print usage
        print err.msg
        raise SystemExit(2)

    try:
        if config.daemon:
            drive_daemon(config)
        elif mode.DEBDEV and restarter.PARENT:
            print 'starting child server'
            restarter.launch_child()
        else:
            print 'starting server'
            start_server(config)
    except KeyboardInterrupt:
        pass
