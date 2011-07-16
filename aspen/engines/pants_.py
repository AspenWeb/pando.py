from aspen.engines import ThreadEngine
import pants
from pants.contrib.http import HTTPServer
from pants.contrib.wsgi import WSGIConnector


class Engine(CooperativeEngine):

    def bind(self):
        connector = WSGIConnector(self.website)
        self.server = HTTPServer(connector)
        self.server.listen( host=self.website.address[0]
                          , port=self.website.address[1]
                           )

    def start(self):
        pants.engine.start()

    def stop(self):
        pants.engine.stop()

    def start_restarter(self, check_all):
        pants.cycle(check_all, 0.5)
