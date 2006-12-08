"""Define the main program loop.
"""
import logging
import os
import sys
import time
from optparse import OptionError
from os.path import isdir, isfile, join

from aspen import daemon, mode, restarter
from aspen.server import CherryPyWSGIServer as Server
from aspen.config import ConfigError, Configuration, usage


__version__ = '~~VERSION~~'


log = logging.getLogger('aspen')



def _main(config):
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


def main(argv=None):
    """Initial phase of config parsing and setup.
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        config = Configuration(argv)
        RUNFG = config.command == 'runfg'
        
        if not RUNFG: 
            
            # Manipulate a daemon.
            # ====================
        
            var = join(config.paths.root, '__', 'var')
            if not isdir(var):
                os.makedirs(var)
            pidpath = join(var, 'aspen.pid')
            logpath = join(var, 'aspen.log')
            
            d = daemon.Daemon(stdout=logpath, stderr=logpath, pidfile=pidpath)


            # Start/stop wrappers
            # ===================

            def start():
                print "starting daemon"
                d.start()

            def stop():
                if not isfile(pidpath):
                    print "no pidfile; process not running?"
                    return
                    
                try:
                    sys.stdout.write('stopping daemon')
                    sys.stdout.flush()
                    d.stop()
                except OSError, exc:
                    print
                    print str(exc) + "; unclean shutdown?"
                else:
                    # @@: Verify that the process has indeed stopped.
    
                    then = time.time()
                    while (then+1) > time.time():
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        time.sleep(0.2) 
                    print 'done'


            # Branch
            # ======

            if config.command == 'start':
                if isfile(pidpath):
                    print "pidfile exists; already running? unclean shutdown?"
                    raise SystemExit(1)
                start()
                
            elif config.command == 'stop':
                stop()
                raise SystemExit(0)
                
            elif config.command == 'restart':
                stop()
                start()

            else: # safety net
                raise ConfigError("Bad command: %s" % config.command)            
        
    except ConfigError, err:
        print >> sys.stderr, usage
        print >> sys.stderr, err.msg
        raise SystemExit(2)


    try:
        if RUNFG and mode.DEBDEV and restarter.PARENT:
            restarter.launch_child()
        else:
            _main(config)
    except KeyboardInterrupt:
        pass
