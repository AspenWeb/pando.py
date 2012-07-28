import collections
import time

from aspen.network_engines import CooperativeEngine
from aspen.sockets import packet
from aspen.sockets.loop import Die
import tornado.ioloop
import tornado.httpserver
import tornado.wsgi


class TornadoBuffer(collections.deque):
    """Model a buffer of items.

    There are two of these for each Socket, one for incoming message payloads
    and one for outgoing message objects.

    Here's what the flow looks like:

        wire => [msg, msg, msg, msg, msg, msg, msg, msg] => resource
        wire <= [msg, msg, msg, msg, msg, msg, msg, msg] <= resource

    """

    def __init__(self, name, socket=None):
        """Takes a string and maybe a socket.

        If given a socket, we will try to play nice with its loop.

        """

        # It feels like it's going to take deeper rewiring to get *.sock files
        # working with Tornado callbacks.
        raise NotImplementedError("Sorry, for now please use a different "
                                  "networking library in order to use *.sock "
                                  "files.")

        collections.deque.__init__(self)
        self._socket = socket
        self._name = name

    put = collections.deque.appendleft
    get = collections.deque.pop
    empty = lambda d: not bool(d)


    # flush
    # =====
    # Used for outgoing buffer.

    def flush(self):
        """Return an iterable of bytestrings or None.
        """
        if not self.empty():
            return self.__flusher()
        return None

    def __flusher(self):
        """Yield strings.

        We unload bytestrings as fast as we can until we run out of time or
        bytestrings. On my MacBook Pro I am seeing between 500 and 1000
        messages dumped in 2ms--without any WSGI/HTTP/TCP overhead. We always
        yield at least one bytestring to avoid deadlock.

        This generator is instantiated in self.flush.

        """
        if not self.empty():
            yield packet.frame(self.get())
        timeout = time.time() + (0.007) # We have 7ms to dump bytestrings. Go!
        while not self.empty() and time.time() < timeout:
            yield packet.frame(self.get())


    # next
    # ====
    # Used for incoming buffer.

    def next(self):
        """Return the next item from the queue.

        The first time this is called, we lazily instantiate the generator at
        self._blocked. Subsequent calls are directed directly to that
        generator's next method.

        """
        self._blocked = self._blocked()
        self.next = self._next
        return self.next()

    def _next(self):
        try:
            return self._blocked.next()
        except StopIteration:
            # When the _blocked generator discovers Die and breaks, the
            # effect is a StopIteration here. It's a bug if this happens
            # other than when we are disconnecting the socket.
            assert self._socket is not None
            assert self._socket.loop.please_stop

    def _blocked(self):
        """Yield items from self forever.

        This generator is lazily instantiated in self.next. It is designed to
        cooperate with ThreadedLoop. XXX Oh yeah?

        """
        if self._socket is None:    # We're on a Channel.
            while 1:
                yield self.get()
        else:                       # We're on a Socket.
            while not self._socket.loop.please_stop:
                out = self.get()
                if out is Die:
                    break # will result in a StopIteration
                yield out


class TornadoLoop(object):

    def __init__(self, socket):
        self.socket = socket
        self.please_stop = False

    def __call__(self):
        while not self.please_stop:
            self.socket.tick()

    def start(self):
        pass

    def stop(self):
        self.please_stop = True
        self.socket.incoming.put(Die)


class Engine(CooperativeEngine):

    checker = None

    def bind(self):
        container = tornado.wsgi.WSGIContainer(self.website)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(self.website.network_address[1])

    def sleep(self, seconds):
        time.sleep(seconds)

    def start(self):
        try:
            tornado.ioloop.IOLoop.instance().start()
        except SystemExit:
            pass

    def start_checking(self, check_all):
        self.checker = tornado.ioloop.PeriodicCallback(check_all, 500)
        self.checker.start()

    def stop_checking(self):
        self.checker.stop()

    Buffer = TornadoBuffer
    Loop = TornadoLoop

