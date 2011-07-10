import time
import threading

from aspen._cherrypy.wsgiserver import CherryPyWSGIServer
from aspen.server import BaseEngine


class Engine(BaseEngine):

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


    socket_threads = []
    def spawn_socket_handler(self, socket):
        """Given a Socket object, spawn a [micro]thread to loop it.
        """
        t = threading.Thread(target=socket.loop)
        t.daemon = True
        t.start()
        self.socket_threads.append(t)
