"""Define the main program loop.

This is actually pretty complicated, due to configuration, daemonization, and
restarting options. Here are the objects defined below:

  1. PIDFiler -- as a daemon, manages our pidfile
  2. server_factory -- returns a wsgiserver.CherryPyWSGIServer instance
  3. start_server -- starts the server, with error trapping
  4. drive_daemon -- manipulates Aspen as a daemon
  5. main -- main callable, natch

"""
import base64
import os
import signal
import socket
import stat
import sys
import threading
import time
import traceback
from os.path import isdir, isfile, join

from aspen import mode, restarter
from aspen._configuration import ConfigurationError, Configuration, usage
from aspen.website import Website
from aspen.wsgiserver import CherryPyWSGIServer as Server


if 'win' in sys.platform:
    WINDOWS = True
    Daemon = None # daemonization not available on Windows; @@: service?
else:
    WINDOWS = False
    from aspen.daemon import Daemon # this actually fails on Windows; needs pwd


__version__ = '~~VERSION~~'
__all__ = ['configuration', 'conf', 'paths', '']


# Configuration API
# =================

configuration = None # an aspen._configuration.Configuration instance
conf = None # an aspen._configuration.ConfFile instance
paths = None # an aspen._configuration.Paths instance
CONFIGURED = False

globals_ = globals()

ROOT_SPLIT = os.sep + '__' + os.sep
def find_root(argv=None):
    if argv is None:
        argv = sys.argv
    script_path = argv and argv[0] or ''
    if not script_path.startswith(os.sep):
        script_path = os.path.join(os.getcwd(), script_path)
    return script_path.split(ROOT_SPLIT)[0]

def configure(argv=None):
    if argv is None:
        argv = ['--root', find_root()]
    global globals_
    globals_['configuration'] = Configuration(argv)
    globals_['conf'] = configuration.conf
    globals_['paths'] = configuration.paths
    globals_['CONFIGURED'] = True

def unconfigure(): # for completeness and tests
    global globals_
    globals_['configuration'] = None
    globals_['conf'] = None
    globals_['paths'] = None
    globals_['CONFIGURED'] = False
    mode.set('development')


def get_perms(path):
    return stat.S_IMODE(os.stat(path)[stat.ST_MODE])


class PIDFiler(threading.Thread):
    """Thread to continuously monitor a pidfile, keeping our pid in the file.

    This is run when we are a daemon, in the child process. It checks every
    second to see if the file exists, recreating it if not. It also rewrites the
    file every 60 seconds, just in case the contents have changed, and resets
    the mode to 0600 just in case it has changed.

    """

    stop = threading.Event()
    path = '' # path to the pidfile
    pidcheck_timeout = 60 # seconds between pidfile writes
    pidfile_mode = 0600 # the permission bits on the pidfile

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def write(self):
        open(self.path, 'w+').write(str(os.getpid()))
        self.set_perms()

    def set_perms(self):
        os.chmod(self.path, self.pidfile_mode)

    def run(self):
        """Pidfile is initially created and finally destroyed by our Daemon.
        """
        self.set_perms()
        last_pidcheck = 0
        while not self.stop.isSet():
            if not isfile(self.path):
                print "no pidfile; recreating"
                sys.stdout.flush()
                self.write()
            elif (last_pidcheck + self.pidcheck_timeout) < time.time():
                self.write()
                last_pidcheck = time.time()
            time.sleep(1)
        if isfile(self.path): # sometimes we beat handlesigterm
            os.remove(self.path)

pidfiler = PIDFiler() # must actually set pidfiler.path before starting


CLEANUPS = []

def register_cleanup(func):
    CLEANUPS.append(func)

def cleanup():
    if CLEANUPS:
        print "cleaning up ..."
        for func in CLEANUPS:
            func()


def website_factory(argv=None):
    """Return an aspen.website.Website instance.
    """
    if not CONFIGURED:
        if argv is None:
            argv = sys.argv[1:]
        configure(argv) # sets globals, e.g., configuration
    configuration.load_plugins() # user modules loaded here
    website = Website(configuration)
    for middleware in configuration.middleware:
        website = middleware(website)
    return website


def server_factory():
    """Return an aspen.wsgiserver.CherryPyWSGIServer instance.
    """

    website = website_factory()

    server = Server(configuration.address, website, configuration.threads)
    server.protocol = "HTTP/%s" % configuration.http_version
    server.version = "Aspen/%s" % __version__


    # Monkey-patch server to support restarting.
    # ==========================================
    # Giving server a chance to shutdown cleanly largely avoids the terminal
    # screw-up bug that plagued httpy < 1.0.

    if restarter.CHILD:
        def tick():
            Server.tick(server)
            if restarter.should_restart():
                print "restarting ..."
                server.stop()
                cleanup()
                raise SystemExit(75)
        server.tick = tick


    return server


def start_server():
    """Get a server object and start it up.
    """

    server = server_factory() # factored out to ease testing


    # Define a shutdown handler and attach to signals.
    # ================================================

    def shutdown(signum, frame, exit=True):
        msg = ""
        if signum is not None:
            msg = "caught "
            msg += { signal.SIGINT:'SIGINT'
                   , signal.SIGTERM:'SIGTERM'
                    }.get(signum, "signal %d" % signum)
            msg += ", "
        print msg + "shutting down"
        sys.stdout.flush()
        server.stop()
        cleanup()                                           # user hook
        if not WINDOWS:
            if configuration.sockfam == socket.AF_UNIX:     # clean up socket
                try:
                    os.remove(configuration.address)
                except EnvironmentError, exc:
                    print "error removing socket:", exc.strerror
        if pidfiler.isAlive():                              # we're a daemon
            pidfiler.stop.set()
            pidfiler.join()

        if exit:
            raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)


    # Start the server.
    # =================
    # And gracefully handle exit conditions.

    print "aspen starting on %s" % str(configuration.address)
    sys.stdout.flush()
    while 1:
        try:
            server.start()
        except SystemExit, exc:
            print "exiting with code %d" % exc.code
            raise
        except:
            print "recovering from critical error:"
            print traceback.format_exc()
            shutdown(None, None, False)
            time.sleep(1)


def drive_daemon():
    """Manipulate a daemon or become one ourselves.
    """

    # Locate some paths.
    # ==================

    __ = join(configuration.paths.root, '__')
    if isdir(__):
        var = join(__, 'var')
        if not isdir(var):
            os.mkdir(var)
        pidfile = join(var, 'aspen.pid')
        logpath = join(var, 'aspen.log')
    else:
        key = ' '.join([str(configuration.address), configuration.paths.root])
        key = base64.urlsafe_b64encode(key)
        pidfile = os.sep + join('tmp', 'aspen-%s.pid' % key)
        logpath = '/dev/null'


    # Instantiate the daemon.
    # =======================

    daemon = Daemon(stdout=logpath, stderr=logpath, pidfile=pidfile)


    # Start/stop wrappers
    # ===================
    # Set the logpath perms here; pidfile perms taken care of by pidfiler.

    def start():
        daemon.start()
        if not logpath == '/dev/null':
            os.chmod(logpath, 0600)
        pidfiler.path = pidfile
        pidfiler.start()
        start_server()


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

        kill_timeout = 5

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
                print "%d STILL going; sending SIGKILL and quitting" % pid
                kill(signal.SIGKILL)
                raise SystemExit(1)
            nattempts += 1

            last_attempt = time.time()
            while 1:
                if not isfile(pidfile):
                    return # daemon has stopped
                elif (last_attempt + kill_timeout) < time.time():
                    break # daemon hasn't stopped; time to escalate
                else:
                    time.sleep(0.2)


    # Branch
    # ======

    if configuration.command == 'start':
        if isfile(pidfile):
            print "pidfile already exists with pid %s" % open(pidfile).read()
            raise SystemExit(1)
        start()

    elif configuration.command == 'status':
        if isfile(pidfile):
            pid = int(open(pidfile).read())
            command = "ps auxww|grep ' %d .*aspen'|grep -v grep" % pid
            # @@: I, um, doubt this command is portable. :^)
            os.system(command)
            raise SystemExit(0)
        else:
            print "daemon not running"
            raise SystemExit(0)

    elif configuration.command == 'stop':
        stop()
        raise SystemExit(0)

    elif configuration.command == 'restart':
        stop()
        start()


def main(argv=None):
    """Initial phase of configuration, and daemon/restarter/server branch.
    """

    if argv is None:
        argv = sys.argv[1:]

    try:
        configure(argv)
    except ConfigurationError, err:
        print usage
        print err.msg
        raise SystemExit(2)

    try:
        if configuration.daemon:
            drive_daemon()
        elif mode.DEBDEV and restarter.PARENT:
            print 'launching child process'
            restarter.launch_child()
        elif restarter.CHILD:

            # Make sure we restart when conf files change.
            # ============================================

            __ = configuration.paths.__
            if __:
                for path in ( join(__, 'etc', 'apps.conf')
                            , join(__, 'etc', 'aspen.conf')
                            , join(__, 'etc', 'handlers.conf')
                            , join(__, 'etc', 'middleware.conf')
                             ):
                    if isfile(path):
                        restarter.track(path)

            print 'starting child server'
            start_server()
        else:
            print 'starting server'
            start_server()

    except KeyboardInterrupt:
        pass
