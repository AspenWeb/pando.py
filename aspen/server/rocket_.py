import sys
import time
import threading

try:
    import rocket 
except ImportError:
    print >> sys.stderr, ("Please install rocket in order to "
                          "run aspen with the rocket engine.")
    raise 


server = None


def start(website):
    global server
    server = rocket.CherryPyWSGIServer(website.address, website)
    server.start()

def stop():
    server.stop()

def start_restarter(check_all):

    def loop():
        while True:
            try:
                check_all()
            except SystemExit:
                server.stop()
            time.sleep(0.5)

    checker = threading.Thread(target=loop)
    checker.daemon = True
    checker.start()

