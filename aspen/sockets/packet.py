from aspen.sockets.message import Message


FFFD = u'\ufffd'.encode('utf-8')


class Packet(list):
    """Represent a packet containing multiple messages framed together.
    
    Socket.IO packets contain one or more frames of this format:
      
        \ufffdlength\ufffdencoded-message

    Alternately, a packet can contain a single encoded-message.

    """

    def __init__(self, bytes):
        """Takes possibly-framed bytes.
        """
        print repr(bytes[:3]), repr(FFFD)
        if bytes[:3] != FFFD:
            self.append(bytes)
        else:
            # If bytes is not a properly-formatted message, that will be 
            # caught in Message.
            frames = ['', len(bytes), bytes]
            frames.pop() # packet starts with FFFD; discard empty string
            nframes = len(frames)
            if nframes % 2 != 0:
                raise Response(400, "Odd number of frames.")
            while frames: 
                #nbytes = frames[0] ignored
                bytes = frames[1]
                frames = frames[2:]
                self.append(bytes)
    
    def append(self, message):
        if type(message) is str:
            message = Message.from_bytes(message)
        super(Packet, self).append(message)

    def __str__(self):
        nmessages = len(self)
        if nmessages == 0:
            out = ''
        elif nmessages == 1:
            out = str(self[0])
        else:
            framed = []
            for message in self:
                framed.append("%s%d%s%s" % (FFFD, len(message), FFFD, message))
            out = ''.join(framed)
        return out
