import atexit
import logging
import os
import socket
import sys
import traceback

import aspen
from aspen import restarter
from aspen.website import Website
from aspen.wsgiserver import CherryPyWSGIServer as BaseServer


log = logging.getLogger('aspen.server')


class Server(BaseServer):

    def __init__(self, configuration):
        """Extend to take a Configuration object.
        """

        self.configuration = configuration
        self.protocol = "HTTP/%s" % configuration.http_version
        self.version = "Aspen/%s" % aspen.__version__

        website = Website(self)
        for middleware in configuration.middleware:
            website = middleware(website)
        self.website = website

        # super() vs. BaseClass.__init__():
        # http://mail.python.org/pipermail/python-list/2006-February/367002.html
        BaseServer.__init__( self
                           , configuration.address
                           , website
                           , configuration.threads
                            )
    
        atexit.register(self.stop)
   

    def start(self):
        """Extend to support filesystem monitoring.
        """
        log.warn("starting on %s" % str(self.configuration.address))
   
        if aspen.mode.DEBDEV:
            log.info("configuring filesystem monitor")
            __ = self.configuration.paths.__
            if __:
                for path in ( os.path.join(__, 'etc', 'apps.conf')
                            , os.path.join(__, 'etc', 'aspen.conf')
                            , os.path.join(__, 'etc', 'handlers.conf')
                            , os.path.join(__, 'etc', 'logging.conf')
                            , os.path.join(__, 'etc', 'middleware.conf')
                             ):
                    if os.path.isfile(path):
                        restarter.monitor(path)
            restarter.start_monitoring()
        
        BaseServer.start(self)


    def stop(self):
        """Extend for additional cleanup.
        """
        log.debug("cleaning up server")
        sys.stdout.flush()
        BaseServer.stop(self)
        if 'win' not in sys.platform: 
            if self.configuration.sockfam == socket.AF_UNIX: # clean up socket
                try:
                    os.remove(configuration.address)
                except EnvironmentError, exc:
                    log.error("error removing socket:", exc.strerror)
        # pidfile removed in __init__.py:main_loop
        # restarter stopped in ipc/restarter.py:_atexit


    if restarter.CHILD:
        def tick(self):
            """Extend to support restarting when we are restarter.CHILD.

            Note that when using aspen.main_loop, Server is only ever
            instantiated within restarter.CHILD.

            """
            BaseServer.tick(self)
            if restarter.should_restart():
                log.info("restarting")
                raise SystemExit(75) # will trigger self.stop via atexit

