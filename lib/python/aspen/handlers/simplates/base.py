import os
import stat
import threading
import traceback
import sys

try:
    import aspen
except: # defaults when run apart from Aspen
    ENCODING = 'UTF-8'
    MODE_STPROD = True 
    MODE_DEBUG = False
else:
    ENCODING = aspen.conf.simplates.get('encoding', 'UTF-8')
    MODE_STPROD = aspen.mode.STPROD
    MODE_DEBUG = aspen.mode.DEBUG


FORM_FEED = chr(12) # == '\x0c', ^L, ASCII page break


class LoadError(StandardError):
    """Represent a problem parsing a simplate.
    """


class Entry:
    """An entry in the global simplate cache.
    """

    fspath = ''         # The filesystem path [string]
    modtime = None      # The timestamp of the last change [datetime.datetime]
    lock = None         # Access control for this record [threading.Lock]
    truple = None       # A post-processed version of the data [3-tuple]
    exc = None          # Any exception in reading or compilation [Exception]

    def __init__(self):
        """Populate with dummy data or an actual db entry.
        """
        self.fspath = ''
        self.modtime = 0
        self.lock = threading.Lock()
        self.truple = ()


class BaseSimplate(object):
    """This object provides one public method: load_simplate.

    Framework-specific subclasses must meet three requirements:

        - implement compile_template (take a string, return a template object)
        - implement __call__ with the WSGI signature
        - something at or below __call__ must perform the simplate algorithm

    In staging and production modes, this class implements a thread-safe cache.
    Cache entries are keyed to filesystem paths, and expire when the modtime of
    the file changes. If parsing the file into a simplate raises an Exception,
    then that is cached as well, and will be raised on further calls until the
    entry expires as usual.

    @@: constrain the size of the cache? prune based on age and use?

    """

    __cache = dict()        # cache, global to all Simplate subclasses [dict]
    __locks = None          # access controls for self.__cache [Locks]


    def __init__(self):
        """
        """
        self.__cache = {}
        class Locks:
            checkin = threading.Lock()
            checkout = threading.Lock()
        self.__locks = Locks()


    # Subclass Hook
    # =============

    def compile_template(self, template):
        """Given a string, return a template object.

        This is to be overriden in subclasses. This is your hook for compiling
        templates before they are cached. Default is to return the template
        string untouched.

        """
        return template


    # Load
    # ====

    def _load_simplate_uncached(self, fspath):
        """Given a filesystem path, return three objects.

        A simplate is a template with two optional Python components at the head
        of the file, delimited by an ASCII form feed (also called a page break, FF,
        ^L, 0xc, 12). The first Python section is exec'd when the simplate is
        first called, and the namespace it populates is saved for all subsequent
        runs (so make sure it is thread-safe!). The second Python section is exec'd
        within the template namespace each time the template is rendered.

        Two more things:

            [simplates]
            encoding = latin-1

        ... and ...

            __file__

        """
        encoding = ENCODING
        simplate = open(fspath).read().decode(encoding)

        numff = simplate.count(FORM_FEED)
        if numff == 0:
            script = imports = ""
            template = simplate
        elif numff == 1:
            imports = ""
            script, template = simplate.split(FORM_FEED)
            script += FORM_FEED
        elif numff == 2:
            imports, script, template = simplate.split(FORM_FEED)
            imports += FORM_FEED
            script += FORM_FEED
        else:
            raise SyntaxError( "Simplate <%s> may have at most two " % fspath
                             + "form feeds; it has %d." % numff
                              )

        # Standardize newlines.
        # =====================
        # compile requires \n, and doing it now makes the next line easier.

        imports = imports.replace('\r\n', '\n')
        script = script.replace('\r\n', '\n')


        # Pad the beginning of the script section so we get accurate tracebacks.
        # ======================================================================

        script = ''.join(['\n' for n in range(imports.count('\n'))]) + script


        # Prep our cachable objects and return.
        # =====================================

        namespace = dict(__file__=fspath)
        script = compile(script, fspath, 'exec')
        template = self.compile_template(template)

        exec compile(imports, fspath, 'exec') in namespace

        return (namespace, script, template)


    def _load_simplate_cached(self, fspath):
        """Given a filesystem path, return three objects.
        """

        # Check out an entry.
        # ===================
        # Each entry has its own lock, and "checking out" an entry means
        # acquiring that lock. If a simplate isn't yet in our cache, we first
        # "check in" a new dummy entry for it (and prevent other threads from
        # adding the same simplate), which will be populated presently.

        #thread_id = threading.currentThread().getName()[-1:] # for debugging
        #call_id = ''.join([random.choice(string.letters) for i in range(5)])

        self.__locks.checkout.acquire()
        try: # critical section
            if fspath in self.__cache:

                # Retrieve an already cached simplate.
                # ====================================
                # The cached entry may be a dummy. The best way to guarantee we
                # will catch this case is to simply refresh our entry after we
                # acquire its lock.

                entry = self.__cache[fspath]
                entry.lock.acquire()
                entry = self.__cache[fspath]

            else:

                # Add a new entry to our cache.
                # =============================

                dummy = Entry()
                dummy.fspath = fspath
                dummy.lock.acquire()
                self.__locks.checkin.acquire()
                try: # critical section
                    if fspath in self.__cache:
                        # Someone beat us to it. @@: can this actually happen?
                        entry = self.__cache[fspath]
                    else:
                        self.__cache[fspath] = dummy
                        entry = dummy
                finally:
                    self.__locks.checkin.release()

        finally:
            self.__locks.checkout.release() # Now that we've checked out our
                                            # simplate, other threads are free
                                            # to check out other simplates.


        # Process the simplate.
        # =====================

        try: # critical section

            # Decide whether it's a hit or miss.
            # ==================================

            modtime = os.stat(fspath)[stat.ST_MTIME]
            if entry.modtime == modtime:                            # cache hit
                if entry.exc is not None:
                    raise entry.exc
            else:                                                   # cache miss
                try:
                    entry.truple = self._load_simplate_uncached(fspath)
                    entry.exc = None
                except Exception, exception:
                    # NB: Old-style string exceptions will still raise.
                    entry.exc = ( LoadError(traceback.format_exc())
                                , sys.exc_info()[2]
                                 )


            # Check the simplate back in.
            # ===========================

            self.__locks.checkin.acquire()
            try: # critical section
                entry.modtime = modtime
                self.__cache[fspath] = entry
                if entry.exc is not None:
                    if MODE_DEBUG:
                        print >> sys.stderr, entry.exc[0]
                        pdb.post_mortem(entry.exc[1])
                    raise entry.exc[0]
            finally:
                self.__locks.checkin.release()

        finally:
            entry.lock.release()


        # Return
        # ======
        # Avoid mutating the cached namespace dictionary.

        namespace, script, template = entry.truple
        namespace = namespace.copy()
        return (namespace, script, template)


    # Set API to cached or not based on mode.
    # =======================================

    if MODE_STPROD:
        load_simplate = _load_simplate_cached
    else:
        load_simplate = _load_simplate_uncached
