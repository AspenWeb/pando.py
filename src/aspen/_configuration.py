"""Define configuration objects.

    1. validator_address -- called in a couple places
    2. optparse -- command line interface
    3. paths -- path storage
    4. ConfFile -- represents a configuration file
    5. Configuration -- puts it all together

This module is so-named because we place an instance of Configuration in the
global aspen namespace.

"""
import logging
import os
import socket
import sys
import optparse
import ConfigParser
from os.path import join, isdir, realpath

from aspen import load, mode


log = logging.getLogger('aspen.configuration')
COMMANDS = ('start', 'status', 'stop', 'restart', 'runfg')
WINDOWS = 'win' in sys.platform
if not WINDOWS:
    import pwd


class ConfigurationError(StandardError):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        StandardError.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


def validate_address(address):
    """Given a socket address string, return a tuple (sockfam, address).

    This is called from a couple places, and is a bit complex.

    """

    if address[0] in ('/','.'):
        if WINDOWS:
            raise ConfigurationError("Can't use an AF_UNIX socket on Windows.")
            # but what about named pipes?
        sockfam = socket.AF_UNIX
        # We could test to see if the path exists or is creatable, etc.
        address = realpath(address)

    elif address.count(':') > 1:
        sockfam = socket.AF_INET6
        # @@: validate this, eh?

    else:
        sockfam = socket.AF_INET
        # Here we need a tuple: (str, int). The string must be a valid
        # IPv4 address or the empty string, and the int -- the port --
        # must be between 0 and 65535, inclusive.


        # Break out IP and port.
        # ======================

        if isinstance(address, (tuple, list)):
            if len(address) != 2:
                raise err
            ip, port = address
        elif isinstance(address, basestring):
            if address.count(':') != 1:
                raise err
            ip_port = address.split(':')
            ip, port = [i.strip() for i in ip_port]
        else:
            raise err


        # IP
        # ==

        if not isinstance(ip, basestring):
            raise err
        elif ip == '':
            ip = '0.0.0.0' # IP defaults to INADDR_ANY for AF_INET; specified
                           # explicitly to avoid accidentally binding to
                           # INADDR_ANY for AF_INET6.
        else:
            try:
                socket.inet_aton(ip)
            except socket.error:
                raise err


        # port
        # ====
        # Coerce to int. Must be between 0 and 65535, inclusive.

        if isinstance(port, basestring):
            if not port.isdigit():
                raise err
            else:
                port = int(port)
        elif isinstance(port, int) and not (port is False):
            # already an int for some reason (called interactively?)
            pass
        else:
            raise err

        if not(0 <= port <= 65535):
            raise err


        # Success!
        # ========

        address = (ip, port)


    return address, sockfam


# optparse
# ========
# Does this look ugly to anyone else? It works I guess.

def callback_address(option, opt, value, parser_):
    """Must be a valid AF_INET or AF_UNIX address.
    """
    address, sockfam = validate_address(value)
    parser_.values.address = address
    parser_.values.sockfam = sockfam


def callback_log_level(option, opt, value, parser_):
    """
    """
    try:
        level = getattr(logging, value.upper())
    except AttributeError:
        msg = "Bad log level: %s" % value
        raise optparse.OptionValueError(msg)
    parser_.values.log_level = level


def callback_root(option, opt, value, parser_):
    """Expand the root directory path and make sure the directory exists.
    """
    value = realpath(value)
    if not isdir(value):
        msg = "%s does not point to a directory" % value
        raise optparse.OptionValueError(msg)
    parser_.values.root = value


usage = "aspen [options] [start,stop,&c.]; --help for more"
optparser = optparse.OptionParser(usage=usage)

optparser.add_option( "-a", "--address"
                    , action="callback"
                    , callback=callback_address
                    , default=('0.0.0.0', 8080)
                    , dest="address"
                    , help="the IP or Unix address to bind to [:8080]"
                    , type='string'
                     )
#optparser.add_option( "-l", "--log_filter"
#                    , default=''
#                    , dest="log_filter"
#                    , help="a subsystem filter for logging []"
#                    , type='string'
#                     )
optparser.add_option( "-m", "--mode"
                    , choices=[ 'debugging', 'deb', 'development', 'dev'
                              , 'staging', 'st', 'production', 'prod'
                               ]
                    , default='development'
                    , dest="mode"
                    , help=( "one of: debugging, development, staging, "
                           + "production [development]"
                            )
                    , type='choice'
                     )
optparser.add_option( "-r", "--root"
                    , action="callback"
                    , callback=callback_root
                    , default=os.getcwd()
                    , dest="root"
                    , help="the root publishing directory [.]"
                    , type='string'
                     )
#optparser.add_option( "-v", "--log_level"
#                    , action="callback"
#                    , callback=callback_log_level
#                    , choices=[ 'notset', 'debug', 'info', 'warning', 'error'
#                              , 'critical'
#                               ]
#                    , default='info'
#                    , dest="log_level"
#                    , help=( "the level below which messages will be stiffled "
#                           + "[warning]"
#                            )
#                    , type='choice'
#                     )


class Paths:
    """Junkdrawer for a few paths we like to keep around.
    """

    def __init__(self, root):
        """Takes the website's filesystem root.

            root    website's filesystem root: /
            __      magic directory: /__
            lib     python library: /__/lib/python2.x
            plat    platform-specific python library: /__/lib/plat-<foo>

        If there is no magic directory, then __, lib, and plat are all None. If
        there is, then lib and plat are added to sys.path.

        """
        self.root = root
        self.__ = join(self.root, '__')
        if not isdir(self.__):
            self.__ = None
            self.lib = None
            self.plat = None
        else:
            lib = join(self.__, 'lib', 'python'+sys.version[:3])
            self.lib = isdir(lib) and lib or None

            plat = join(lib, 'plat-'+sys.platform)
            self.plat = isdir(plat) and plat or None

            pkg = join(lib, 'site-packages')
            self.pkg = isdir(pkg) and pkg or None

            for path in (lib, plat, pkg):
                if isdir(path):
                    sys.path.insert(0, path)


class ConfFile(ConfigParser.RawConfigParser):
    """Represent a configuration file.

    This class wraps the standard library's RawConfigParser class. The
    constructor takes the path of a configuration file. If the file does not
    exist, you'll get an empty object. Use either attribute or key access on
    instances of this class to return section dictionaries. If a section doesn't
    exist, you'll get an empty dictionary.

    """

    def __init__(self, filepath):
        ConfigParser.RawConfigParser.__init__(self)
        self.read([filepath])

    def __getitem__(self, name):
        return self.has_section(name) and dict(self.items(name)) or {}

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.__class__.__dict__:
            return self.__class__.__dict__[name]
        else:
            return self.__getitem__(name)


    # Iteration API
    # =============
    # mostly for testing

    def iterkeys(self):
        return iter(self.sections())
    __iter__ = iterkeys

    def iteritems(self):
        for k in self:
            yield (k, self[k])

    def itervalues(self):
        for k in self:
            yield self[k]


class Configuration(load.Mixin):
    """Aggregate configuration from several sources.
    """

    args = None # argument list as returned by OptionParser.parse_args
    conf = None # a ConfFile instance
    optparser = None # an optparse.OptionParser instance
    opts = None # an optparse.Values instance per OptionParser.parse_args
    paths = None # a Paths instance

    address = None # the AF_INET, AF_INET6, or AF_UNIX address to bind to
    command = None # one of restart, runfg, start, status, stop [runfg]
    daemon = None # boolean; whether to daemonize
    defaults = None # tuple of default resource names for a directory
    sockfam = None # one of socket.AF_{INET,INET6,UNIX}
    threads = None # the number of threads in the pool


    def __init__(self, argv):
        """Takes an argv list, gives it straight to optparser.parse_args.
        """

        # Initialize parsers.
        # ===================
        # The 'root' knob can only be specified on the command line.

        opts, args = optparser.parse_args(argv)
        paths = Paths(opts.root)                # default handled by optparse
        conf = ConfFile(join(paths.root, '__', 'etc', 'aspen.conf'))

        self.args = args
        self.conf = conf
        self.optparser = optparser
        self.opts = opts
        self.paths = paths


        # command/daemon
        # ==============
        # Like root, 'command' can only be set on the command line.

        command = args and args[0] or 'runfg'
        if command not in COMMANDS:
            raise ConfigurationError("Bad command: %s" % command)
        daemon = command != 'runfg'
        if daemon and WINDOWS:
            raise ConfigurationError("Can only daemonize on UNIX.")

        self.command = command
        self.daemon = daemon


        # address/sockfam & mode
        # ======================
        # These can be set either on the command line or in the conf file.

        if 'address' in conf.main:
            address, sockfam = validate_address(conf.main['address'])
        else:
            address = opts.address              # default handled by optparse
            sockfam = getattr(opts, 'sockfam', socket.AF_INET)

        if 'mode' in conf.main:
            mode_ = conf.main['mode']
        else:
            mode_ = opts.mode                   # default handled by optparse

        self.address = address
        self.sockfam = sockfam
        mode.set(mode_)


        # aspen.conf
        # ==========
        # These remaining options are only settable in aspen.conf. Just a
        # couple for now.

        # defaults
        # --------

        defaults = conf.main.get('defaults', ('index.html', 'index.htm'))
        if isinstance(defaults, basestring):
            if ',' in defaults:
                defaults = [d.strip() for d in defaults.split(',')]
            else:
                defaults = defaults.split()
        self.defaults = tuple(defaults)


        # threads
        # -------

        threads = conf.main.get('threads', 10)
        if isinstance(threads, basestring):
            if not threads.isdigit():
                raise TypeError( "thread count not a positive integer: "
                               + "'%s'" % threads
                                )
            threads = int(threads)
            if not threads >= 1:
                raise ValueError("thread count less than 1: '%d'" % threads)
        self.threads = threads



#        # user
#        # ----
#        # Must be a valid user account on this system.
#
#        if WINDOWS:
#            raise ConfigurationError("can't switch users on Windows")
#        try:
#            user = pwd.getpwnam(candidate)[2]
#        except KeyError:
#            raise ConfigurationError("bad user: '%s'" % candidate)
#        return user


        # Logging
        # =======
        # When run in the foreground, always log to stdout/stderr; otherwise,
        # always log to __/var/log/error.log.x, rotating per megabyte.
        #
        # Currently we just support throttling from the command line based on
        # subsystem and level.


#        #logging.basicConfig(format=FORMAT)
#
#        handler = logging.StreamHandler()
#        handler.addFilter(logging.Filter(self.opts.log_filter))
#        form = logging.Formatter(logging.BASIC_FORMAT)
#        handler.setFormatter(form)
#        logging.root.addHandler(handler)
#        logging.root.setLevel(self.opts.log_level)
#        log.debug("logging configured")
