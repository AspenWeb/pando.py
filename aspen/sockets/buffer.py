from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import Queue
import sys
import threading
import time

from aspen.sockets import packet
from aspen.sockets.loop import Die


if sys.version_info < (2, 6): # patch
    threading._Event.is_set = threading._Event.isSet


class ThreadedBuffer(Queue.Queue):
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
        Queue.Queue.__init__(self)
        self._socket = socket
        self._name = name


    # flush
    # =====
    # Used for outgoing buffer.

    def flush(self):
        """Return an iterable of bytestrings or None.
        """
        if self.queue:
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
        if self.queue:
            yield packet.frame(self.get())
        timeout = time.time() + (0.007) # We have 7ms to dump bytestrings. Go!
        while self.queue and time.time() < timeout:
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
            assert self._socket.loop.please_stop.is_set()

    def _blocked(self):
        """Yield items from self forever.

        This generator is lazily instantiated in self.next. It is designed to
        cooperate with ThreadedLoop.

        """
        if self._socket is None:    # We're on a Channel.
            while 1:
                yield self.get()
        else:                       # We're on a Socket.
            while not self._socket.loop.please_stop.is_set():
                out = self.get()
                if out is Die:
                    break # will result in a StopIteration
                yield out
