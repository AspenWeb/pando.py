import collections
import time


from aspen.sockets import packet


class ThreadedBuffer(collections.deque):
    """Model a buffer of items.
  
    There are two of these for each Socket, one for incoming message payloads
    and one for outgoing message objects.

    Here's what the flow looks like: 

        wire => [msg, msg, msg, msg, msg, msg, msg, msg] => resource
        wire <= [msg, msg, msg, msg, msg, msg, msg, msg] <= resource

    Deques are thread-safe:

        http://mail.python.org/pipermail/python-dev/2004-July/046350.html

    """

    def __init__(self, messages=None):
        """Given a sequence of Messages, buffer them.
        """
        if messages is not None:
            for message in messages:
                self.put(message)
        self.__blocked = self.__blocked()


    # put/get
    # =======

    put = collections.deque.appendleft
    get = collections.deque.pop

    
    # flush
    # =====
    # Used for outgoing buffer.

    def flush(self):
        """Return an iterable of bytestrings or None.
        """
        if self:
            return self.__flusher()
        return None

    def __flusher(self):
        """Yield strings.

        We unload bytestrings as fast as we can until we run out of time or
        bytestrings. On my MacBook Pro I am seeing between 500 and 1000
        messages dumped in 2ms--without any WSGI/HTTP/TCP overhead. We always
        yield at least one bytestring to avoid deadlock.

        This generator is instantiated in flush.

        """
        if self:
            yield packet.frame(self.get())
        timeout = time.time() + (0.007) # We have 7ms to dump bytestrings. Go!
        while self and time.time() < timeout:
            yield packet.frame(self.get())


    # next 
    # ====
    # Used for incoming buffer.

    def next(self):
        return self.__blocked.next()

    def __blocked(self):
        """Yield items from self forever.

        This generator is instantiated in __init__.

        """
        while 1:
            if self:
                yield self.get()
            time.sleep(0.010)

Buffer = ThreadedBuffer
