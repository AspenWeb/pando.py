import time
import threading

from aspen._cherrypy.wsgiserver import CherryPyWSGIServer
from aspen.network_engines import ThreadedEngine


class Engine(ThreadedEngine):

    cp_server = None # a CherryPyWSGIServer instance

    def bind(self):
        self.cp_server = CherryPyWSGIServer( self.website.network_address
                                           , self.website
                                            )

        # Work around a Jython bug.
        # =========================
        # http://bugs.jython.org/issue1848
        # http://stackoverflow.com/questions/1103487/
        try:                        # >= 2.6
            import platform
            if platform.python_implementation() == 'Jython':
                self.cp_server.nodelay = False
        except AttributeError:      # < 2.6
            import sys
            if sys.platform.startswith('java'):
                self.cp_server.nodelay = False

    def start(self):
        self.cp_server.start()

    def stop(self):
        self.cp_server.stop()

    def start_checking(self, check_all):

        def loop():
            while True:
                try:
                    check_all()
                except SystemExit:
                    self.cp_server.interrupt = SystemExit
                time.sleep(0.5)

        checker = threading.Thread(target=loop)
        checker.daemon = True
        checker.start()
