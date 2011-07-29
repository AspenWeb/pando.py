import socket
import sys
import time

import eventlet
import eventlet.wsgi
from aspen.engines import CooperativeEngine
from aspen.sockets import packet
from aspen.sockets.loop import Die
from eventlet.queue import LightQueue


class DevNull:
    def write(self, msg):
        pass

class EventletBuffer(LightQueue):
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
        LightQueue.__init__(self)
        self._socket = socket
        self._name = name


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
        cooperate with ThreadedLoop.

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


class EventletLoop(object):
   
    def __init__(self, socket):
        self.socket = socket
        self.please_stop = False
        self.greenthread = None

    def __call__(self):
        while not self.please_stop:
            self.socket.tick()

    def start(self):
        self.greenthread = eventlet.spawn(self)

    def stop(self):
        self.please_stop = True
        self.socket.incoming.put(Die)
        self.greenthread.wait()


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

    def sleep(self, seconds):
        eventlet.sleep(seconds)

    def start(self):
        eventlet.wsgi.server(self.eventlet_socket, self.website, log=DevNull())

    def start_restarter(self, check_all):
        def loop():
            while True:
                check_all()
                self.sleep(0.5)
        eventlet.spawn_n(loop)

    Buffer = EventletBuffer
    Loop = EventletLoop
