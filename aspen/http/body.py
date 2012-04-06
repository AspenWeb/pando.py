import cgi

from aspen.http.mapping import Mapping


class Body(Mapping):
    """Represent the body of an HTTP request.
    """

    def __init__(self, content_type, s_iter):
        """Takes an encoding type and an iterable of bytestrings.
        
        If the Mapping API is used (in/one/all/has), then the iterable will be
        read and parsed as media of type application/x-www-form-urlencoded or
        multipart/form-data, according to enctype.

        """
        self.content_type = content_type 
        self.s_iter = s_iter

    _raw = ""
    def raw(self):
        if not self._raw:
            self._raw = "".join(self.s_iter)
        return self._raw
    raw = property(raw) # lazy


    # Extend Mapping to parse.
    # ========================

    def _parse(self):
        if self.content_type.startswith('multipart/form-data'):
            return cgi.FieldStorage( fp = cgi.StringIO(self.raw)
                                   , environ = {} # XXX?
                                   , strict_parsing = True 
                                    )

    def __contains__(self, name):
        self._parse()
        return super(Body, self).__contains__(name);

    def all(self, name, default=None):
        self._parse()
        return super(Body, self).all(name, default);

    def one(self, name, default=None):
        self._parse()
        return super(Body, self).one(name, default);




if 0:
    if not environ.get('SERVER_SOFTWARE', '').startswith('Rocket'):
        # normal case
        self._body = environ['wsgi.input'].read()
    else:
        # rocket engine

        # Email from Rocket guy: While HTTP stipulates that you shouldn't
        # read a socket unless you are specifically expecting data to be
        # there, WSGI allows (but doesn't require) for that
        # (http://www.python.org/dev/peps/pep-3333/#id25).  I've started
        # support for this (if you feel like reading the code, its in the
        # connection class) but this feature is not yet production ready
        # (it works but it way too slow on cPython).
        #
        # The hacky solution is to grab the socket from the stream and
        # manually set the timeout to 0 and set it back when you get your
        # data (or not).
        # 
        # If you're curious, those HTTP conditions are (it's better to do
        # this anyway to avoid unnecessary and slow OS calls):
        # - You can assume that there will be content in the body if the
        #   request type is "POST" or "PUT"
        # - You can figure how much to read by the "CONTENT_LENGTH" header
        #   existence with a valid integer value
        #   - alternatively "CONTENT_TYPE" can be set with no length and
        #     you can read based on the body content ("content-encoding" =
        #     "chunked" is a good example).
        #
        # Here's the "hacky solution":

        _tmp = environ['wsgi.input']._sock.timeout
        environ['wsgi.input']._sock.settimeout(0) # equiv. to non-blocking
        try:
            self._raw_body = environ['wsgi.input'].read()
        except Exception, exc:
            if exc.errno != 35:
                raise
            self._raw_body = ""
        environ['wsgi.input']._sock.settimeout(_tmp)


