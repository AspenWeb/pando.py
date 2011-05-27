import time
import threading

from aspen._cherrypy.wsgiserver import CherryPyWSGIServer


server = None


def init(website):
    global server
    server = CherryPyWSGIServer(website.address, website)

def start(website):
    server.start()

def stop():
    print "stopping cherrypy"
    server.stop()

def start_restarter(check_all):

    def loop():
        while True:
            try:
                check_all()
            except SystemExit:
                server.interrupt = SystemExit
            time.sleep(0.5)

    checker = threading.Thread(target=loop)
    checker.daemon = True
    checker.start()
