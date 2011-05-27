import sys

from pants import cycle, engine
from pants.contrib.http import HTTPServer
from pants.contrib.wsgi import WSGIConnector


def init(website):
    global server
    connector = WSGIConnector(website)
    server = HTTPServer(connector)
    server.listen(host=website.address[0], port=website.address[1])

def start(website):
    engine.start()

def stop():
    engine.stop()

def start_restarter(check_all):
    cycle(check_all, 0.5)

