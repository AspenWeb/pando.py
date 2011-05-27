import sys

try:
    from pants import cycle, engine
    from pants.contrib.http import HTTPServer
    from pants.contrib.wsgi import WSGIConnector
except ImportError:
    print >> sys.stderr, ("Please install Pants in order to"
                          "run aspen with the Pants engine.")
    raise

def start(website):
    connector = WSGIConnector(website)
    server = HTTPServer(connector)
    server.listen(host=website.address[0], port=website.address[1])
    engine.start()

def stop():
    engine.stop()

def start_restarter(check_all):
    # TODO Figure out whether this is the correct approach.
    cycle(check_all, 0.5)

