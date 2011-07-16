import threading
from aspen.sockets.buffer import ThreadedBuffer


class BaseEngine(object):

    def __init__(self, name, website):
        """Takes an identifying string and a WSGI application.
        """
        self.name = name
        self.website = website

    def bind(self):
        """Bind to a socket, based on website.sockfam and website.address.
        """

    def start(self):
        """Start listening on the socket.
        """

    def stop(self):
        """Stop listening on the socket.
        """

    def start_restarter(self, check_all):
        """Start a loop that runs check_all every half-second.
        """

    def stop_restarter(self):
        """Stop the loop that runs check_all (optional).
        """

class ThreadedEngine(BaseEngine):
    """An engine that uses threads for concurrent persistent sockets.
    """

    def spawn_socket_loop(self, socket):
        """Given a Socket object, spawn a thread to loop it.

        Our architecture here is one thread per persistent socket. Depending on
        the transport we probably have another thread already occupied with the
        HTTP side of the request, from the CherryPy/Rocket threadpool. Assuming
        the thread pool is larger than our concurrent user base, we have two
        threads per persistent connection, in addition to the thread burden of
        any stateless HTTP traffic.

        """
        t = threading.Thread(target=socket.loop)
        t.daemon = True
        t.start()

    Buffer = ThreadedBuffer
    
class CooperativeEngine(BaseEngine):
    """An engine that assumes cooperative scheduling for persistent sockets.
    """

    def spawn_socket_loop(self, socket):
        """Given a Socket object, start it's main loop.

        The expectation here is that the buffer implementation in use will take
        care of cooperative scheduling. So when someone calls socket.recv() in
        one of their socket resources, that will block for them but in a
        cooperative way.

        """
        socket.loop()

    Buffer = NotImplemented
