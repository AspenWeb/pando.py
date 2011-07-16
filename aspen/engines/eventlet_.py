import socket
import sys
    
import eventlet
import eventlet.wsgi
from aspen.engines import CooperativeEngine


class DevNull:
    def write(self, msg):
        pass


class Engine(CooperativeEngine):

    eventlet_socket = None # a socket, per eventlet

    def bind(self):
        self.eventlet_socket = eventlet.listen( self.website.address
                                              , self.website.sockfam
                                               )
        if eventlet.version_info <= (0, 9, 15):
            # Work around https://bitbucket.org/which_linden/eventlet/issue/86/
            if sys.platform[:3] != "win":
                self.eventlet_socket.setsockopt( socket.SOL_SOCKET
                                               , socket.SO_REUSEADDR, 1
                                                )

    def start(self):
        eventlet.wsgi.server(self.eventlet_socket, self.website, log=DevNull())

    def start_restarter(self, check_all):
        def loop():
            while True:
                check_all()
                eventlet.sleep(0.5)
        eventlet.spawn_n(loop)

    def spawn_socket_handler(socket):
        eventlet.spawn_n(socket.loop)
