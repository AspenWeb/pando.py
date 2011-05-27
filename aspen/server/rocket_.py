import sys
import time
import threading

import rocket 


server = None


def init(website):
    global server
    server = rocket.CherryPyWSGIServer(website.address, website)

def start(website):
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

