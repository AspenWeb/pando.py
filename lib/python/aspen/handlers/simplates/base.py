import threading

import aspen


FORM_FEED = chr(12) # == '\x0c', ^L, ASCII page break


class BaseSimplate(object):
    """This object has API for cached simplate loading.

    Framework-specific subclasses must meet three requirements:

        - implements compile_template (takes a string, returns a template object)
        - __call__ implements the WSGI signature
        - something at or below __call__ performs the simplate algorithm

    """

    def __init__(self):
        """
        """
        self.__cache = dict()
        self.__lock = threading.Lock()


    def compile_template(self, template):
        """Given a string, return a template object.

        This is to be overriden in subclasses. This is your hook for compiling
        templates before they are cached.

        """
        raise NotImplementedError


    # Wrappers around __build
    # =======================

    def __load_uncached(self, fspath):
        """Given a filesystem path, return three objects.
        """
        return self.__build(fspath)


    def __load_cached(self, fspath):
        """Given a filesystem path, return three objects.
        """
        # @@ check modtime
        if fspath not in self.__cache:
            self.__lock.acquire()
            try: # critical section


                if key not in self.__cache: # were we in fact blocking?
                    self.__cache[fspath] = self.__build(fspath)
            finally:
                self.__lock.release()

        namespace, script, template = self.__cache[fspath]
        namespace = namespace.copy() # avoid mutating the cached copy
        return namespace, script, template


    if aspen.mode.STPROD:   # cached
        load = __load_cached
    else:                   # uncached
        load = __load_uncached


    def __build(self, fspath):
        """Given a filesystem path, return a three objects.

        A simplate is a template with two optional Python components at the head
        of the file, delimited by an ASCII form feed (also called a page break, FF,
        ^L, \x0c, 12). The first Python section is exec'd when the simplate is
        first called, and the namespace it populates is saved for all subsequent
        runs (so make sure it is thread-safe!). The second Python section is exec'd
        within the template namespace each time the template is rendered.

        Two more things:

            [simplates]
            encoding = latin-1

        ... and ...

            __file__

        """
        encoding = aspen.conf.simplates.get('encoding', 'UTF-8')
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
        # @@: maybe remove the -2 now that we add FORM_FEED back to sections?

        script = ''.join(['\n' for n in range(imports.count('\n')-2)]) + script


        # Prep our cachable objects and return.
        # =====================================

        namespace = dict(__file__=fspath)
        script = compile(script, fspath, 'exec')
        template = self.compile_template(template)

        exec compile(imports, fspath, 'exec') in namespace

        return (namespace, script, template)
