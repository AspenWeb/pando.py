"""Define the main program loop.

Roadmap:

    0.3 -- WSGI
    0.x -- alpha quality, no 0.x.x, just 0.x, as many as we need

    1.0c1 -- release candidate
    1.0.0 -- final

"""
import os
import sys

from aspen import mode, restarter

try:
    import subprocess
    have_subprocess = True
except ImportError:
    have_subprocess = False


__version__ = '~~VERSION~~'


RESTART_FLAG = '_ASPEN_RESTART_FLAG'


def _main(argv):

    import logging
    import os
    import sys
    from optparse import OptionError
    from os.path import join

    from aspen.server import CherryPyWSGIServer as Server
    from aspen.config import ConfigError, Configuration, usage
    from aspen.website import Website


    log = logging.getLogger('aspen')


    # Configure.
    # ==========

    try:
        config = Configuration(argv)
        website = Website(config)
    except ConfigError, err:
        print >> sys.stderr, usage
        print >> sys.stderr, err.msg
        raise SystemExit(2)


    # Wrap the website in a WSGI stack and instantiate a Server.
    # ==========================================================

    for app in config.middleware:
        website = app(website)
    server = Server(config.address, website)


    # Set up restarting support.
    # ==========================
    # We monkey-patch Server to check our monitor thread.
    #
    # BLAM!!! This is actually a really good way to do it. In the old httpy
    # (< 1.0), we had a serious problem when a restart happened during a Pdb
    # session; it would screw up stdin/stdout and the terminal would be all
    # screwy. By calling server.stop() before exiting, we ensure that all
    # requests finish sanely -- including any requests blocked for Pdb --
    # before exiting. Nice!

    if RESTART_FLAG in os.environ:
        monitor = restarter.Monitor()
        def tick():
            Server.tick(server)
            if not monitor.isAlive():
                server.stop()
                raise SystemExit(3)
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


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    try:
        if have_subprocess and mode.devdeb and RESTART_FLAG not in os.environ:
            print "starting with restarter ..."
            args = [sys.executable] + sys.argv
            new_env = os.environ.copy()
            new_env[RESTART_FLAG] = 'Yes please.'
            while 1:
                retcode = subprocess.call(args, env=new_env)
                if retcode != 3:
                    raise SystemExit(retcode)
        else:                                               # main layer
            _main(argv)
    except KeyboardInterrupt:
        pass
