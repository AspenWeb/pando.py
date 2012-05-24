import pants
from aspen.network_engines import CooperativeEngine
from pants.contrib.http import HTTPServer
from pants.contrib.wsgi import WSGIConnector


class Engine(CooperativeEngine):

    def bind(self):
        connector = WSGIConnector(self.website)
        self.server = HTTPServer(connector)
        self.server.listen( host=self.website.network_address[0]
                          , port=self.website.network_address[1]
                           )

    def start(self):
        pants.engine.start()

    def stop(self):
        pants.engine.stop()

    def start_checking(self, check_all):
        pants.cycle(check_all, 0.5)
