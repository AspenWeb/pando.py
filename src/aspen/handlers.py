"""A few default handlers for aspen.
"""
import mimetypes
import rfc822
import os
import stat
from email import message_from_file, message_from_string

from aspen import mode
from aspen.httpy import Response
from aspen.utils import is_valid_identifier


# A couple simple handlers.
# =========================

def HTTP404(environ, start_response):
    raise Response(404)

def pyscript(environ, start_response):
    """Execute the script pseudo-CGI-style.
    """

    context = dict(request=environ)
    context['response'] = Response()
    context['__file__'] = environ['aspen.fp'].name

    fp = environ['aspen.fp']
    del environ['aspen.fp']
    try:
        exec fp in context
    except SystemExit:
        pass
    return context['response']


# A moderately complex one.
# =========================
# XXX: look at Luke Arno's ACK GPL and some others ... Etags? Iteration?

def static(environ, start_response):
    """Serve a static file off of the filesystem.

    In staging and deployment modes, we honor any 'If-Modified-Since'
    header, an HTTP header used for caching.

    """

    path = environ['PATH_TRANSLATED']
    ims = environ.get('HTTP_IF_MODIFIED_SINCE', '')


    # Get basic info from the filesystem and start building a response.
    # =================================================================

    stats = os.stat(path)
    mtime = stats[stat.ST_MTIME]
    size = stats[stat.ST_SIZE]
    content_type = mimetypes.guess_type(path)[0] or 'text/plain'
    response = Response(200)


    # Support 304s, but only in deployment mode.
    # ==========================================

    if mode.stprod:
        if ims:
            mod_since = rfc822.parsedate(ims)
            last_modified = time.gmtime(mtime)
            if last_modified[:6] <= mod_since[:6]:
                response.code = 304


    # Finish building the response and return it.
    # ===========================================

    response.headers['Last-Modified'] = rfc822.formatdate(mtime)
    response.headers['Content-Type'] = content_type
    response.headers['Content-Length'] = size
    if response.code != 304:
        response.body = open(path).read()
    return response


# And a rather complex handler.
# =============================

class Simplate:

    charset = 'UTF-8'

    def __init__(self, website):
        """Given a filesystem path to a master template, load it.

        If path does not point to a file, then we become a passthrough.

        """
        self.website = website
        if website.paths.__ is None:
            self.defaults = {}
            self.master = None
        else:
            path = os.path.join(website.paths.__, 'etc', 'simplate.html')
            self.path = path
            if os.path.isfile(path):
                msg = message_from_file(open(self.path))
                body = msg.get_payload().decode(self.charset)
                self.defaults = dict()
                for key, val in msg.items():
                    key = key.decode(self.charset)
                    val = val.decode(self.charset)
                    if not is_valid_identifier(key):
                        raise BadKey(key, path)
                    self.defaults[key] = val
                self.master = Template(body)
            else:
                self.defaults = {}
                self.master = None


    def __call__(self, environ, start_response):
        """Takes a Response object and populates it.

        We perform two levels of substitution: first, on the specific template
        at hand; then, on the master template. The namespace for each is the
        same (defaults plus keywords), with the addition of the substituted
        specific template as 'body' in the master template substitution.

        """

        # Need to reimplement/cleanup simplates.
        # ======================================
        return static(environ, start_response)


        if self.master is not None:
            if not isinstance(response.body, unicode):
                response.body = response.body.decode(self.charset)

            # XXX: Does email.message.Message only use str, not unicode?
            msg = message_from_string(response.body.encode(self.charset))
            body = msg.get_payload().decode(self.charset)
            local = Template(body)
            local_d = dict()
            for key, val in msg.items():
                key = key.decode(self.charset)
                val = val.decode(self.charset)
                if not is_valid_identifier(key):
                    raise BadKey(key, path)
                local_d[key] = val

            context = self.defaults.copy()
            context.update(local_d)
            context[u'body'] = local.substitute(context, False)

            response.body = self.master.substitute(context, False)
            del response.headers['Content-Length']
            del response.headers['Content-Type']

        return response


# The following is a hacked version of string.Template to wire in a
# case-sensitivity option. It was submitted to Python as a patch:
#
#  http://sourceforge.net/tracker/index.php?func=detail&aid=1528167&group_id=5470&atid=305470
#
# The patch was rejected, but I haven't updated this module yet.

####################################################################
import re as _re


class _TemplateMetaclass(type):
    pattern = r"""
    %(delim)s(?:
      (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
      (?P<named>%(id)s)      |   # delimiter and a Python identifier
      {(?P<braced>%(id)s)}   |   # delimiter and a braced identifier
      (?P<invalid>)              # Other ill-formed delimiter exprs
    )
    """

    def __init__(cls, name, bases, dct):
        super(_TemplateMetaclass, cls).__init__(name, bases, dct)
        if 'pattern' in dct:
            pattern = cls.pattern
        else:
            pattern = _TemplateMetaclass.pattern % {
                'delim' : _re.escape(cls.delimiter),
                'id'    : cls.idpattern,
                }
        cls.pattern = _re.compile(pattern, _re.IGNORECASE | _re.VERBOSE)


class Template:
    """A string class for supporting $-substitutions."""
    __metaclass__ = _TemplateMetaclass

    delimiter = '$'
    idpattern = r'[_a-z][_a-z0-9]*'

    def __init__(self, template, case_sensitive=True):
        self.template = template
        self.case_sensitive = bool(case_sensitive)

    # Search for $$, $identifier, ${identifier}, and any bare $'s

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(True)
        if not lines:
            colno = 1
            lineno = 1
        else:
            colno = i - len(''.join(lines[:-1]))
            lineno = len(lines)
        raise ValueError('Invalid placeholder in string: line %d, col %d' %
                         (lineno, colno))

    def _lower(self, mapping):
        """Given a mapping, return the same mapping with all keys lower-cased.
        """
        _mapping = {}
        for k, v in sorted(mapping.items()):
            k = k.lower()
            if k not in _mapping:
                _mapping[k] = v
        return _mapping

    def substitute(self, *args, **kws):
        if len(args) > 2:
            raise TypeError('Too many positional arguments')
        case_sensitive = self.case_sensitive
        if len(args) == 2:
            case_sensitive = args[1]
        case = case_sensitive and (lambda x: x) or self._lower
        if args:
            mapping = case(args[0])
            mapping.update(case(kws))
        else:
            mapping = case(kws)

        # Helper function for .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                if not case_sensitive:
                    named = named.lower()
                val = mapping[named]
                # We use this idiom instead of str() because the latter will
                # fail if val is a Unicode containing non-ASCII characters.
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

    def safe_substitute(self, *args, **kws):
        if len(args) > 2:
            raise TypeError('Too many positional arguments')
        case_sensitive = self.case_sensitive
        if len(args) == 2:
            case_sensitive = args[1]
        case = case_sensitive and (lambda x: x) or self._lower
        if args:
            mapping = case(args[0])
            mapping.update(case(kws))
        else:
            mapping = case(kws)

        # Helper function for .sub()
        def convert(mo):
            named = mo.group('named')
            if named is not None:
                if not case_sensitive:
                    named = named.lower()
                try:
                    # We use this idiom instead of str() because the latter
                    # will fail if val is a Unicode containing non-ASCII
                    return '%s' % (mapping[named],)
                except KeyError:
                    return self.delimiter + named
            braced = mo.group('braced')
            if braced is not None:
                if not case_sensitive:
                    braced = braced.lower()
                try:
                    return '%s' % (mapping[braced],)
                except KeyError:
                    return self.delimiter + '{' + braced + '}'
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return self.delimiter
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)



####################################################################