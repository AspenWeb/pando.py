import diesel
from aspen.server import BaseEngine
from diesel.protocols import wsgi


class Engine(BaseEngine):

    app = None # a diesel app instance

    def bind(self):
        self.app = wsgi.WSGIApplication( self.website
                                       , self.website.address[1]
                                       , self.website.address[0]
                                        )

    def start(self):
        self.app.run()

    def stop(self):
        try:
            self.app.halt()
        except diesel.app.ApplicationEnd:
            pass # Only you can prevent log spam.

    def start_restarter(self, check_all):
        def loop():
            while True:
                check_all()
                diesel.sleep(0.5)
        self.app.add_loop(diesel.Loop(loop))
