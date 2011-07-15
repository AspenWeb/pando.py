import collections
import time

from aspen.sockets import FFFD, packet
from aspen.sockets.message import Message


class Buffer(collections.deque):
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
                self.push(message)
        self.__blocked = self.__blocked()

    push = collections.deque.appendleft
    pop = collections.deque.pop

    def flush(self):
        """Yield strings.

        We unload bytestrings as fast as we can until we run out of time or
        bytestrings. We always yield at least one bytestring, however, to avoid
        deadlock.

        """
        if self:
            yield str(self.pop())
        timeout = time.time() + (0.020)
        while self and time.time() < timeout:
            yield str(self.pop())

    def next(self):
        return self.__blocked.next()

    def __blocked(self):
        """Yield items from self forever.

        This generator is instantiated in __init__.

        """
        while 1:
            if self:
                yield self.pop()
            time.sleep(0.010)

