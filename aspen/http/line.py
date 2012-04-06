import urlparse
import urllib

from aspen import Response
from aspen.http.querystring import Querystring


class Line(unicode):

    __slots__ = ['method', 'url', 'version', 'raw']

    def __new__(cls, method, url, version):
        """Takes three bytestrings.
        """
        raw = " ".join([method, url, version])
        method = Method(method)
        url = URL(url)
        version = Version(version)
        line = u" ".join([method, url, version.decoded])
        obj = super(Line, cls).__new__(cls, line)
        obj.method = method
        obj.url = url
        obj.version = version
        obj.raw = raw
        return obj
    
    def __repr__(self):
        return u"<Line(unicode): %s>" % self


class Method(unicode):

    def __new__(cls, bytes):
        try:
            method = bytes.decode('ASCII').upper()
        except UnicodeDecodeError:
            raise Response(400)
        obj = super(Method, cls).__new__(cls, method)
        obj.raw = bytes
        return obj
    
    def __repr__(self):
        return u"<Method(unicode): %s>" % self


class URL(unicode):
   
    def __new__(cls, bytes):
        url = bytes.decode('utf-8') # XXX really?
        obj = super(URL, cls).__new__(cls, url)
        obj.raw = bytes
        obj.parsed = urlparse.urlparse(url)
        obj.path = Path(obj.parsed[2]) # further populated by Website
        obj.querystring = Querystring(obj.parsed[4])
        return obj

    def __repr__(self):
        return u"<URL(unicode): %s>" % self


class Path(dict):
    # Populated by aspen.website.Website.

    def __init__(self, bytes):
        self.raw = bytes

    def __str__(self):
        return self.raw

    def __repr__(self):
        return u"<Path(dict): %s>" % self.keys()


class Version(tuple):

    def __new__(cls, bytes):
        http, version = bytes.split('/')    # ("HTTP", "1.1")
        parts = version.split('.')          # (1, 1)
        try:
            major, minor = int(parts[0]), int(parts[1])
        except ValueError:                  # (1, 2, 3) or ('foo', 'bar')
            raise Response(400)

        obj = super(Version, cls).__new__(cls, (major, minor))
        obj.raw = bytes                     # HTTP/1.1
        obj.decoded = bytes.decode('utf-8') # warty?
        return obj

    def __repr__(self):
        return u"<Version(tuple): %s>" % self
