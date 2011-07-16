import time
import threading

import rocket 
from aspen.engines import BaseEngine


class Engine(ThreadedEngine):
    
    rocket_server = None # a rocket.CherryPyWSGIServer instance

    def bind(self):
        self.rocket_server = rocket.CherryPyWSGIServer( self.website.address
                                                      , self.website
                                                       )

    def start(self):
        self.rocket_server.start()

    def stop(self):
        self.rocket_server.stop()

    def start_restarter(self, check_all):

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
