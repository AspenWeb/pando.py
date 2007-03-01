import threading

try:
    from aspen import mode
except ImportError:
    try:
        import mode
    except ImportError:
        mode = None


class Cache(object):
    """A simple thread-safe cache; values never expire.
    """

    def __init__(self, build):
        """
        """
        self.build = build
        self.cache = dict()
        self.lock = threading.Lock()

    if (mode is not None) and mode.DEVDEB:              # uncached
        def __getitem__(self, key):
            """Key access always calls build.
            """
            return self.build(key)

    else:                                               # cached
        def __getitem__(self, key):
            """Key access only calls build the first time.
            """
            if key not in self.cache:
                self.lock.acquire()
                try: # critical section
                    if key not in self.cache: # were we in fact blocking?
                        self.cache[key] = self.build(key)
                finally:
                    self.lock.release()
            return self.cache[key]
