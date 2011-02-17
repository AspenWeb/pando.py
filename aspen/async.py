from diesel.util.queue import Queue, QueueTimeout as Timeout

class Quit(Exception):
    """Signal to a simplate that it's client has gone away.
    """
    pass

