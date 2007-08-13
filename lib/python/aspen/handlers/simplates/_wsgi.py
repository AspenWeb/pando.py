import threading
from BaseHTTPServer import BaseHTTPRequestHandler
from os.path import isfile

import aspen


FORM_FEED = chr(12) # == '\x0c', ^L, ASCII page break
RESPONSES = BaseHTTPRequestHandler.responses


class Cache(object):
    """A simple thread-safe cache; values never expire.
    """

    def __init__(self, build):
        """
        """
        self.build = build
        self.cache = dict()
        self.lock = threading.Lock()

    if (aspen.mode is not None) and aspen.mode.DEVDEB:  # uncached
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



class SimpleResponse(object):
    """An HTTP Response message.
    """

    def __init__(self, code=200, body='', headers=None):
        """Takes an int, a string, and a dict. Validation is Task's job.

            - code        an HTTP response code, e.g., 404
            - body        the message body as a string
            - headers     a dictionary of HTTP headers (or list of tuples)

        Body is second because one more often wants to specify a body without
        headers, than a header without a body.

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif not isinstance(body, basestring) and not(isiter(body)):
            raise TypeError("'body' must be a string or an iterator")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")

        self.code = code
        self.body = body
        self.headers = Message()
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers[k] = v


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, RESPONSES.get(self.code, ('???',))[0])


class Simplate(object):
    """Base class for framework-specific simplate implementations.

    This class is instantiated on import when each framework is available, and
    is then wired up in handlers.conf.

    The base implementation uses straight Python string interpolation as its
    templating language.

    """

    # To be overriden
    # ===============

    def build_template(self, template):
        """Given a string, return a framework-specific template object.
        """
        return template

    def update_namespace(self, namespace):
        """Given a dictionary, return it with per-request framework objects.
        """
        return namespace

    def start_response(self, namespace, start_response):
        """Given a namespace and a WSGI start_response function, call it.
        """
        start_response('200 OK', [()])


    # Not intended to be overriden
    # ============================

    def __call__(self, environ, start_response):
        """WSGI contract.
        """
        fspath = environ['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."

        namespace, script, template  = self.__build(fspath) # @@ replace w/ cache call!
        namespace = namespace.copy() # don't mutate the cached version
        namespace['__file__'] = fspath
        namespace['environ'] = environ
        namespace['start_response'] = start_response
        self.update_namespace(namespace)

        if script:
            try:
                exec script in namespace
            except SystemExit:
                pass

        self.start_response(namespace, start_response)

        if 'response' in namespace:
            response = namespace['response']
        else:
            response = [template % namespace]

        return response


    # This should end up in a cache.
    # ==============================

    def __build(self, fspath):
        """Given a filesystem path, return a mapping of namespaces.

        A simplate is a template with two optional Python components at the head
        of the file, delimited by an ASCII form feed (also called a page break, FF,
        ^L, \x0c, 12). The first Python section is exec'd when the simplate is
        first called, and the namespace it populates is saved for all subsequent
        runs (so make sure it is thread-safe!). The second Python section is exec'd
        within the template namespace each time the template is rendered.

        It is a requirement that subclasses do not mutate the import context at
        runtime.

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

        namespace = dict()
        script = compile(script, fspath, 'exec')
        template = self.build_template(template)

        exec compile(imports, fspath, 'exec') in namespace

        return (namespace, script, template)


wsgi = Simplate()