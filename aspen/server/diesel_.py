import sys

import diesel
from diesel.protocols import wsgi


app = None


def init(website):
    global app
    app = wsgi.WSGIApplication(website, website.address[1], website.address[0])

def start(website):
    app.run()

def stop():
    try:
        app.halt()
    except diesel.app.ApplicationEnd:
        pass # Only you can prevent log spam.

def start_restarter(check_all):
    def loop():
        while True:
            check_all
            diesel.sleep(0.5)
    app.add_loop(diesel.Loop(loop))

