import socket
import sys
try:
    import eventlet
    import eventlet.wsgi
except ImportError:
    print >> sys.stderr, ("Please install eventlet in order to "
                          "run aspen with the eventlet engine.")
    raise 

class DevNull:
    def write(self, msg):
        pass

def start(website):
    sock = eventlet.listen(website.address, website.sockfam)
    if eventlet.version_info <= (0, 9, 15):
        # Work around https://bitbucket.org/which_linden/eventlet/issue/86/
        if sys.platform[:3] != "win":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    eventlet.wsgi.server(sock, website, log=DevNull())

def stop():
    pass

def start_restarter(check_all):
    def loop():
        while True:
            check_all()
            eventlet.sleep(0.5)
    eventlet.spawn_n(loop)
