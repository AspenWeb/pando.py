import threading
import time

from aspen.sockets.buffer import ThreadedBuffer
from aspen.sockets.loop import ThreadedLoop


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


# Threaded
# ========

class ThreadedEngine(BaseEngine):
    """An engine that uses threads for concurrent persistent sockets.
    """

    def sleep(self, seconds):
        time.sleep(seconds)

    Buffer = ThreadedBuffer
    Loop = ThreadedLoop
   

# Cooperative
# ===========

class CooperativeEngine(BaseEngine):
    """An engine that assumes cooperative scheduling for persistent sockets.
    """

    def start_socket_loop(self, socket):
        """Given a Socket object, start it's main loop.

        The expectation here is that the buffer implementation in use will take
        care of cooperative scheduling. So when someone calls socket.recv() in
        one of their socket resources, that will block for them but in a
        cooperative way.

        """
        socket.loop()
        return None

    def sleep(self, seconds):
        raise NotImplementedError

    Buffer = NotImplemented
