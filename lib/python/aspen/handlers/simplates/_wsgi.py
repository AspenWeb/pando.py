import threading
from os.path import isfile

from aspen import mode


FORM_FEED = chr(12) # ^L, ASCII page break


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


class Namespaces(object):
    pass



class Simplate(object):
    """Base class for framework-specific simplate implementations.

    This class is instantiated on import when each framework is available, and
    is then wired up in handlers.conf.

    """

    # To be overriden
    # ===============

    response_class = None # override w/ framework's response class
                          # used for "raise SystemExit" semantics.

    def build_template(self, template):
        """Given a string, return a framework-specific template object.
        """
        raise NotImplementedError

    def populate_script_namespace(self, namespace):
        """Given a dictionary, populate it with framework objects.
        """
        raise NotImplementedError

    def populate_template_namespace(self, namespace):
        """Given an empty dictionary, populate it with framework objects.

        The result of this call is updated with the result of namespace_script,
        before being used to render the template.

        """
        raise NotImplementedError


    # Not intended to be overriden
    # ============================

    def __call__(self, environ, start_response):
        """Framework should *not* override this.
        """
        fspath = environ['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."
        namespaces = self.build(fspath)
        start_response
        return []


    def build(fspath):
        """Given a filesystem path, return a Namespaces object.

        A simplate is a template with two optional Python components at the head
        of the file, delimited by an ASCII form feed (also called a page break, FF,
        ^L, \x0c, 12). The first Python section is exec'd when the simplate is
        first called, and the namespace it populates is saved for all subsequent
        runs (so make sure it is thread-safe!). The second Python section is exec'd
        within the template namespace each time the template is rendered.

        It is a requirement that subclasses do not mutate the import context at
        runtime.

        """
        simplate = open(fspath).read().decode('UTF-8')

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

        namespaces = Namespaces()
        namespaces.imports = dict()
        namespaces.script = compile(script, fspath, 'exec')
        namespaces.template = self.build_template(template)

        exec compile(imports, fspath, 'exec') in namespaces.imports

        return namespaces


wsgi = Simplate()