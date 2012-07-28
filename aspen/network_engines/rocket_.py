import time
import threading

import rocket
from aspen.network_engines import ThreadedEngine


class Engine(ThreadedEngine):

    rocket_server = None # a rocket.CherryPyWSGIServer instance

    def bind(self):
        self.rocket_server = rocket.CherryPyWSGIServer( self.website.network_address
                                                      , self.website
                                                       )

    def start(self):
        self.rocket_server.start()

    def stop(self):
        self.rocket_server.stop()

    def start_checking(self, check_all):

        def loop():
            while True:
                try:
                    check_all()
                except SystemExit:
                    self.rocket_server.stop()
                time.sleep(0.5)

        checker = threading.Thread(target=loop)
        checker.daemon = True
        checker.start()
