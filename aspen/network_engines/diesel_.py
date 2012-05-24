import diesel
from aspen.network_engines import CooperativeEngine
from diesel.protocols import wsgi


class Engine(CooperativeEngine):

    diesel_app = None # a diesel diesel_app instance

    def bind(self):
        self.diesel_app = wsgi.WSGIApplication( self.website
                                              , self.website.network_address[1]
                                              , self.website.network_address[0]
                                               )

    def start(self):
        self.diesel_app.run()

    def stop(self):
        try:
            if self.diesel_app is not None:
                self.diesel_app.halt()
        except diesel.app.ApplicationEnd:
            pass # Only you can prevent log spam.

    def start_checking(self, check_all):
        def loop():
            while True:
                check_all()
                diesel.sleep(0.5)
        self.diesel_app.add_loop(diesel.Loop(loop))
