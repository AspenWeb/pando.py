from aspen.server import BaseEngine
from pants import cycle, engine
from pants.contrib.http import HTTPServer
from pants.contrib.wsgi import WSGIConnector


class Engine(BaseEngine):

    def bind(self):
        connector = WSGIConnector(self.website)
        self.server = HTTPServer(connector)
        self.server.listen( host=self.website.address[0]
                          , port=self.website.address[1]
                           )

    def start(self):
        engine.start()

    def stop(self):
        engine.stop()

    def start_restarter(self, check_all):
        cycle(check_all, 0.5)
