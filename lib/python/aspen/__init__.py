"""Main loop
"""
import atexit
import logging
import os
import sys
import tempfile
import traceback

from aspen import mode

# Hack until we unglobalize configuration
__version__ = '~~VERSION~~'

from aspen._configuration import ConfigurationError, Configuration, usage
from aspen.ipc import restarter
from aspen.ipc.pidfile import PIDFile
from aspen.server import Server


#__version__ = '~~VERSION~~'
__all__ = ['configuration', 'conf', 'paths', '']


log = logging.getLogger('aspen')


# Global Configuration
# ====================
# @@: This should go away. See issue #137:
#
#   http://code.google.com/p/aspen/issues/detail?id=137

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
    #global globals_ # @@: do I need to declare this as global?
    globals_['configuration'] = Configuration(argv)
    globals_['conf'] = configuration.conf
    globals_['paths'] = configuration.paths
    globals_['CONFIGURED'] = True
    return configuration

def unconfigure(): # for completeness and tests
    #global globals_
    globals_['configuration'] = None
    globals_['conf'] = None
    globals_['paths'] = None
    globals_['CONFIGURED'] = False
    mode.set('development')


# Main
# ====

def absolutize_root(argv):
    """Absolutize any --root given in argv.

    We need to absolutize any root path, because when we daemonize we chdir in 
    the daemon/parent, so if --root is relative it will break in the child.

    We only run this when we are demonizing. It will have been validated by 
    OptParse by then.

    """
    for i in range(len(argv)):
        val = argv[i]
        if val in ('-r', '--root'):
            root = argv[i+1]
            argv[i+1] = os.path.realpath(root)
            break
        elif val.startswith('-r'):
            root = val[len('-r'):]
            argv[i] = '-r%s' % os.path.realpath(root)
            break
        elif val.startswith('--root='):
            root = val[len('--root='):]
            argv[i] = '--root=%s' % os.path.realpath(root)
            break
    return argv


def main_loop(configuration):
    """Given a configuration object, do daemony things and go into a loop.
    """
    if restarter.PARENT:

        argv = sys.argv[:]

        if configuration.daemon is not None:
            argv = absolutize_root(argv)
            configuration.daemon.drive() # will daemonize or raise SystemExit

        restarter.loop(argv)

    else:
        assert restarter.CHILD # sanity check

        if configuration.daemon is not None:
            configuration.pidfile.write() # only in CHILD of daemon
            atexit.register(configuration.pidfile.remove)

        server = Server(configuration)
        server.start()


def main(argv=None):
    """Configure safely and then run main loop safely.
    """

    if argv is None:
        argv = sys.argv[1:]

    try:
        configuration = configure(argv)
    except ConfigurationError, err:
        print >> sys.stderr, usage
        print >> sys.stderr, err.msg
        sys.exit(2)

    try:
        main_loop(configuration)
    except SystemExit, exc:
        if exc.code == 0:
            log_func = log.debug
        if exc.code != 0:
            log_func = log.info
        
        tb = sys.exc_info()[2]
        while tb.tb_next is not None:
            tb = tb.tb_next
        frame = tb.tb_frame
        filename = os.path.basename(frame.f_code.co_filename)
        location = "%s:%s" % (filename, frame.f_lineno)
        log_func("exiting with exit code %d (from %s)" % (exc.code, location))

        raise # fyi, without this child wasn't terminating

    except KeyboardInterrupt:
        pass
    except:
        log.critical(traceback.format_exc())
        sys.exit(1)

