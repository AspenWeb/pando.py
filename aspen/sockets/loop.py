import threading


class Die:
    pass


class ThreadedLoop(threading.Thread):
    """Model a loop using a thread.

    Our architecture here is one thread per persistent socket. Depending on the
    transport we probably have another thread already occupied with the HTTP
    side of the request, from the CherryPy/Rocket threadpool. Assuming the
    thread pool is larger than our concurrent user base, we have two threads
    per persistent connection, in addition to the thread burden of any
    stateless HTTP traffic.

    """

    def __init__(self, socket):
        """Takes a socket object.
        """
        super(ThreadedLoop, self).__init__()
        self.socket = socket 
        self.please_stop = threading.Event()
        self.daemon = True

    def run(self):
        while not self.please_stop.is_set():
            self.socket.tick()

    def start(self):
        threading.Thread.start(self)

    def stop(self):
        """Stop the socket loop thread.

        We signal to the thread loop to exit as soon as the next blocking
        operation is complete, and then we attempt to unblock one of those
        possible blocking operations: reading the incoming buffer.

        """
        # stop running tick as soon as possible
        self.please_stop.set()

        # unblock reads from incoming
        self.socket.incoming.put(Die)

        # wait for magic to work 
        self.join()

