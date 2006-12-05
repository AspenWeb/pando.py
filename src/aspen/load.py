"""Routines for loading plugin objects based on config file settings.
"""
import cStringIO
import inspect
import logging
import os
from os.path import isdir, isfile, join, realpath

from aspen import colon, utils
from aspen.exceptions import *


log = logging.getLogger('aspen.load')
clean = lambda x: x.split('#',1)[0].strip() # clears comments & whitespace
default_handlers_conf = """\

    catch_all   aspen.rules:catch_all
    isdir       aspen.rules:isdir
    isfile      aspen.rules:isfile
    fnmatch     aspen.rules:fnmatch
    hashbang    aspen.rules:hashbang


    [aspen.handlers:HTTP404]
          isfile
      AND fnmatch *.py[cod]         # hide any compiled Python scripts

    [aspen.handlers:pyscript]
          isfile
      AND fnmatch *.py              # exec python scripts ...
      OR  hashbang                  # ... and anything starting with #!

    [aspen.handlers:default_or_autoindex]
      isdir                         # do smart things for directories

    [aspen.handlers:static]
      catch_all                     # anything else, serve it statically

"""

README_aspen = """\
This directory is served by the application configured on line %d of
__/etc/apps.conf. To wit:

%s

"""

class Handler(object):
    """Represent a function that knows how to obey the rules.

    Some optimization ideas:

      - cache the results of match()
      - evaluate the expression after each rule is added, exit early if False

    """

    handle = None # the actual callable we are tracking
    _rules = None # a list containing the rules
    _funcs = None # a mapping of rulenames to rulefuncs
    _name = '' # the name of the callable

    def __init__(self, rulefuncs, handle):
        """Takes a mapping of rulename to rulefunc, and a WSGI callable.
        """
        self._funcs = rulefuncs
        self.handle = handle

    def __str__(self):
        return "<%s>" % repr(self.handle)
    __repr__ = __str__

    def __eq__(self, other):
        """This is mostly here to ease testing.
        """
        try:
            assert utils.cmp_routines(self.handle, other.handle)
            assert self._rules == other._rules
            assert sorted(self._funcs.keys()) == sorted(other._funcs.keys())
            for k,v in self._funcs.items():
                assert utils.cmp_routines(v, other._funcs[k])
            return True
        except AssertionError:
            return False


    def add(self, rule, lineno):
        """Given a rule string, add it to the rules for this handler.

        The rules are stored in self._rules, the first item of which is a
        two-tuple: (rulename, predicate); subsequent items are three-tuples:
        (boolean, rulename, predicate).

            boolean -- one of 'and', 'or', 'and not'. Any NOT in the conf file
                       becomes 'and not' here.

            rulename -- a name defined in the first (anonymous) section of
                        handlers.conf; maps to a rule callable in self._funcs

            predicate -- a string that is meaningful to the rule callable

        lineno is for error handling.

        """

        # Tokenize and get the boolean
        # ============================

        if self._rules is None:                 # no rules yet
            self._rules = []
            parts = rule.split(None, 1)
            if len(parts) not in (1, 2):
                msg = "need one or two tokens in '%s'" % rule
                raise HandlersConfError(msg, lineno)
            parts.reverse()
            boolean = None
        else:                                   # we have at least one rule
            parts = rule.split(None, 2)
            if len(parts) not in (2,3):
                msg = "need two or three tokens in '%s'" % rule
                raise HandlersConfError(msg, lineno)

            parts.reverse()
            orig = parts.pop()
            boolean = orig.lower()
            if boolean not in ('and', 'or', 'not'):
                msg = "bad boolean '%s' in '%s'" % (orig, rule)
                raise HandlersConfError(msg, lineno)
            boolean = (boolean == 'not') and 'and not' or boolean


        # Get the rulename and predicate
        # ==============================

        rulename = parts.pop()
        if rulename not in self._funcs:
            msg = "no rule named '%s'" % rulename
            raise HandlersConfError(msg, lineno)
        predicate = parts and parts.pop() or None
        assert len(parts) == 0 # for good measure


        # Package up and store
        # ====================

        if boolean is None:
            _rule = (rulename, predicate)
        else:
            _rule = (boolean, rulename, predicate)

        if _rule in self._rules:
            log.info("duplicate handlers rule: %s [line %d]" % (rule, lineno))
        else:
            self._rules.append(_rule)


    def match(self, pathname):
        """Given a full pathname, return a boolean.

        I thought of allowing rules to return arbitrary values that would then
        be passed along to the handlers. Basically this was to support routes-
        style regular expression matching, but that is an application use case,
        and handlers are specifically not for applications but publications.

        """
        if not self._rules: # None or []
            raise HandlerError, "no rules to match"

        rulename, predicate = self._rules[0]                    # first
        expressions = [str(self._funcs[rulename](pathname, predicate))]

        for boolean, rulename, predicate in self._rules[1:]:    # subsequent
            result = bool(self._funcs[rulename](pathname, predicate))
            expressions.append('%s %s' % (boolean, result))

        expression = ' '.join(expressions)
        return eval(expression) # e.g.: True or False and not True


class Mixin:

    # Apps
    # ====

    def load_apps(self):
        """Return a list of (URI path, WSGI application) tuples.
        """

        # Find a config file to parse.
        # ============================

        apps = []

        try:
            if self.paths.__ is None:
                raise NotImplementedError
            path = join(self.paths.__, 'etc', 'apps.conf')
            if not isfile(path):
                raise NotImplementedError
        except NotImplementedError:
            log.info("No apps configured.")
            return apps


        # We have a config file; proceed.
        # ===============================

        fp = open(path)
        lineno = 0
        urlpaths = []

        for dirpath, dirnames, filenames in os.walk(self.paths.root):
            if 'README.aspen' not in filenames:
                continue
            os.remove(join(dirpath, 'README.aspen'))

        for line in fp:
            lineno += 1
            original = line # for README.aspen
            line = clean(line)
            if not line:                            # blank line
                continue
            else:                                   # specification

                # Perform basic validation.
                # =========================

                if ' ' not in line:
                    msg = "malformed line (no space): '%s'" % line
                    raise AppsConfError(msg, lineno)
                urlpath, name = line.split(None, 1)
                if not urlpath.startswith('/'):
                    msg = "URL path not specified absolutely: '%s'" % urlpath
                    raise AppsConfError(msg, lineno)


                # Instantiate the app on the filesystem.
                # ======================================

                fspath = utils.translate(self.paths.root, urlpath)
                if not isdir(fspath):
                    os.makedirs(fspath)
                    log.info("created app directory '%s'"% fspath)
                readme = join(fspath, 'README.aspen')
                open(readme, 'w+').write(README_aspen % (lineno, original))


                # Determine whether we already have an app for this path.
                # =======================================================

                msg = "URL path is contested: '%s'" % urlpath
                contested = AppsConfError(msg, lineno)
                if urlpath in urlpaths:
                    raise contested
                if urlpath.endswith('/'):
                    if urlpath[:-1] in urlpaths:
                        raise contested
                elif urlpath+'/' in urlpaths:
                    raise contested
                urlpaths.append(urlpath)


                # Load the app, check it, store it.
                # =================================

                obj = colon.colonize(name, fp.name, lineno)
                obj = self._instantiate(obj)
                if not callable(obj):
                    msg = "'%s' is not callable" % name
                    raise AppsConfError(msg, lineno)
                apps.append((urlpath, obj))

        apps.sort()
        apps.reverse()
        return apps


    # Handlers
    # ========

    def load_handlers(self):
        """Return a list of Handler instances.
        """

        # Find a config file to parse.
        # ============================

        user_conf = False
        if self.paths.__ is not None:
            path = join(self.paths.__, 'etc', 'handlers.conf')
            if isfile(path):
                user_conf = True

        if user_conf:
            fp = open(path)
            fpname = fp.name
        else:
            log.info("No handlers configured; using defaults.")
            fp = cStringIO.StringIO(default_handlers_conf)
            fpname = '<default>'


        # We have a config file; proceed.
        # ===============================
        # The conditions in the loop below are not in the order found in the
        # file, but are in the order necessary for correct processing.

        rulefuncs = {} # a mapping of function names to rule functions
        handlers = [] # a list of Handler objects
        handler = None # the Handler we are currently processing
        lineno = 0

        for line in fp:
            lineno += 1
            line = clean(line)
            if not line:                            # blank line
                continue
            elif line.startswith('['):              # new section
                if not line.endswith(']'):
                    raise HandlersConfError("missing end-bracket", lineno)
                if not rulefuncs:
                    raise HandlersConfError("no rules specified yet", lineno)
                name = line[1:-1]
                obj = colon.colonize(name, fpname, lineno)
                if inspect.isclass(obj):
                    obj = obj(self)
                if not callable(obj):
                    msg = "'%s' is not callable" % name
                    raise HandlersConfError(msg, lineno)
                handler = Handler(rulefuncs, obj)
                handlers.append(handler)
                continue
            elif handler is None:                   # anonymous section
                if ' ' not in line:
                    msg = "malformed line (no space): '%s'" % line
                    raise HandlersConfError(msg, lineno)
                rulename, name = line.split(None, 1)
                obj = colon.colonize(name, fpname, lineno)
                obj = self._instantiate(obj)
                if not callable(obj):
                    msg = "'%s' is not callable" % name
                    raise HandlersConfError(msg, lineno)
                rulefuncs[rulename] = obj
            else:                                   # named section
                handler.add(line, lineno)

        return handlers


    # Middleware
    # ==========

    def load_middleware(self):
        """Return a list of (URI path, WSGI middleware) tuples.
        """

        # Find a config file to parse.
        # ============================

        default_stack = []

        try:
            if self.paths.__ is None:
                raise NotImplementedError
            path = join(self.paths.__, 'etc', 'middleware.conf')
            if not isfile(path):
                raise NotImplementedError
        except NotImplementedError:
            log.info("No middleware configured.")
            return default_stack


        # We have a config file; proceed.
        # ===============================

        fp = open(path)
        lineno = 0
        stack = []

        for line in fp:
            lineno += 1
            name = clean(line)
            if not name:                            # blank line
                continue
            else:                                   # specification
                obj = colon.colonize(name, fp.name, lineno)
                obj = self._instantiate(obj)
                if not callable(obj):
                    msg = "'%s' is not callable" % name
                    raise MiddlewareConfError(msg, lineno)
                stack.append(obj)

        stack.reverse()
        return stack


    # Helper
    # ======

    def _instantiate(self, Obj):
        """Given an object, return an instance of the object.
        """
        if inspect.isclass(Obj):
            try:
                obj = Obj(self)
            except TypeError:
                obj = Obj()
        else:
            obj = Obj
        return obj
