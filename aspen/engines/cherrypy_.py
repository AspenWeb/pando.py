import time
import threading

from aspen._cherrypy.wsgiserver import CherryPyWSGIServer
from aspen.engines import ThreadedEngine


class Engine(ThreadedEngine):

    cp_server = None # a CherryPyWSGIServer instance

    def bind(self):
        self.cp_server = CherryPyWSGIServer(self.website.address, self.website)

    def start(self):
        self.cp_server.start()

    def stop(self):
        self.cp_server.stop()

    def start_restarter(self, check_all):

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
