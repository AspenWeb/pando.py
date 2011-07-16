"""Packets.

Socket.IO packets contain one or more frames of this format:
      
    \ufffdlength\ufffdencoded-message

Alternately, a packet can contain a single encoded-message, without framing.

"""
from aspen.sockets import FFFD
from aspen.sockets.message import Message


class Packet(object):
    """Model a Socket.IO packet. It takes bytes and yields Messages.
    """
    
    def __init__(self, bytes):
        self.bytes = bytes

    def __iter__(self):
        """Yield Message objects.
        """
        if self.bytes[:3] != FFFD:
            yield Message.from_bytes(self.bytes)
        else:
            frames = self.bytes.split(FFFD)
            frames = frames[1:] # discard initial empty string
            nframes = len(frames)
            if nframes % 2 != 0:
                msg = "There are an odd number of frames in this packet: " 
                msg += self.bytes
                raise SyntaxError(msg)
            while frames:
                # frames == [nbytes, bytes, nbytes, bytes, ...]
                # We only care about bytes.
                yield Message.from_bytes(frames[1])
                frames = frames[2:]


def frame(bytes):
    bytes = str(bytes)
    return "%s%d%s%s" % (FFFD, len(bytes), FFFD, bytes)
