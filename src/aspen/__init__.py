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


__version__ = '~~VERSION~~'


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
    # We monkey-patch server to check our monitor thread.
    #
    # BLAM!!! This is actually a really good way to do it. In the old httpy
    # (< 1.0), we had a serious problem when a restart happened during a Pdb
    # session; it would screw up stdin/stdout and the terminal would be all
    # screwy. By calling server.stop() before exiting, we ensure that all
    # requests finish sanely -- including any requests blocked for Pdb --
    # before exiting. Nice!

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


def wrap(func, *arg, **kw):
    try:
        func(*arg, **kw)
    except:
        import traceback
        traceback.print_exc()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    try:
        if mode.DEBDEV and restarter.PARENT:
            restarter.launch_child()
        else:
            _main(argv)
    except KeyboardInterrupt:
        pass
