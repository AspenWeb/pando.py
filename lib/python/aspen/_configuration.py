"""Define configuration objects.

    1. validator_address -- called in a couple places
    2. optparse -- command line interface
    3. paths -- path storage
    4. ConfFile -- represents a configuration file
    5. Configuration -- puts it all together

This module is so-named because we place an instance of Configuration in the
global aspen namespace.

"""
import atexit
import base64
import logging
import logging.config
import optparse
import os
import socket
import sys
import tempfile
import ConfigParser
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

from aspen import __version__, load, mode
from aspen.ipc.daemon import Daemon
from aspen.ipc.pidfile import PIDFile

log = logging.getLogger('aspen') # configured below; not used until then
COMMANDS = ('start', 'status', 'stop', 'restart')
WINDOWS = 'win' in sys.platform
#if not WINDOWS:
#    import pwd

LOG_FORMAT = "%(message)s"
LOG_LEVEL = logging.WARNING
LOG_LEVELS = ( 'NIRVANA'    # oo
             , 'CRITICAL'   # 50
             , 'ERROR'      # 40
             , 'WARNING'    # 30
             , 'INFO'       # 20
             , 'DEBUG'      # 10
             , 'NOTSET'     #  0
              )


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
        address = os.path.realpath(address)

    elif address.count(':') > 1:
        sockfam = socket.AF_INET6
        # @@: validate this, eh?

    else:
        sockfam = socket.AF_INET
        # Here we need a tuple: (str, int). The string must be a valid
        # IPv4 address or the empty string, and the int -- the port --
        # must be between 0 and 65535, inclusive.


        err = ConfigurationError("Bad address %s" % str(address))


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


def validate_log_level(log_level):
    """Convert a string to an int.
    """
    if log_level not in LOG_LEVELS:
        msg = "logging level must be one of %s, not %s"
        log_levels = ', '.join(LOG_LEVELS)
        raise ConfigurationError(msg % (log_levels, log_level))
    if log_level == 'NIRVANA':
        log_level = sys.maxint
    else:
        log_level = getattr(logging, log_level)
    return log_level


# optparse
# ========

def callback_address(option, opt, value, parser_):
    """Must be a valid AF_INET or AF_UNIX address.
    """
    address, sockfam = validate_address(value)
    parser_.values.address = address
    parser_.values.sockfam = sockfam
    parser_.values.have_address = True
    parser_.values.raw_address = value 

def callback_root(option, opt, value, parser_):
    """Expand the root directory path and make sure the directory exists.
    """
    dirpath = os.path.realpath(value)
    if not os.path.isdir(dirpath):
        msg = "%s does not point to a directory" % dirpath
        raise optparse.OptionValueError(msg)
    parser_.values.root = dirpath
    parser_.values.raw_root = value

def callback_mode(option, opt, value, parser_):
    """Indicate that we have a mode from the command line.
    """
    parser_.values.mode = value
    parser_.values.have_mode= True
    parser_.values.raw_mode = value

def callback_log_level(option, opt, value, parser_):
    """Convert the string to an int.
    """
    parser_.values.log_level = validate_log_level(value)
    parser_.values.raw_log_level = value

def store_raw(option, opt, value, parser_):
    """Store both the computed and the raw value for get_clean_argv in __init__.
    """
    setattr(parser_.values, option.dest, value)
    setattr(parser_.values, 'raw_'+option.dest, value)


usage = "aspen [options] [restart,start,status,stop]; --help for "\
        "more"
version = """\
aspen, version %s

(c) 2006-2009 Chad Whitacre and contributors
http://www.zetadev.com/software/aspen/
""" % __version__

optparser = optparse.OptionParser(usage=usage, version=version)
optparser.description = """\
Aspen is a Python webserver. If given no arguments or options, it will start in
the foreground serving a website from the current directory on port 8080, based
on configuration files in ./__/etc/, logging to stdout. Full documentation is
on the web at http://www.zetadev.com/software/aspen/.
"""


# Basic
# -----

basic_group = optparse.OptionGroup( optparser
                                  , "Basics"
                                  , "Configure filesystem and network "\
                                    "location, and lifecycle stage."
                                   )
basic_group.add_option( "-a", "--address"
                    , action="callback"
                    , callback=callback_address
                    , default=('0.0.0.0', 8080)
                    , dest="address"
                    , help="the IP or Unix address to bind to [:8080]"
                    , type='string'
                     )
basic_group.add_option( "-m", "--mode"
                    , action="callback"
                    , callback=callback_mode
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
basic_group.add_option( "-r", "--root"
                    , action="callback"
                    , callback=callback_root
                    , default=os.getcwd()
                    , dest="root"
                    , help="the root publishing directory [.]"
                    , type='string'
                     )

optparser.add_option_group(basic_group)


# Logging 
# -------

logging_group = optparse.OptionGroup( optparser
                                    , "Logging"
                                    , "Basic configuration of Python's "\
                                      "logging library; for more complex "\
                                      "needs use a logging.conf file"
                                     )

logging_group.add_option( "-o", "--log-file"
                    , action="callback"
                    , callback=store_raw
                    , default=None
                    , dest="log_file"
                    , help="the file to which messages will be logged; if "\
                           "specified, it will be rotated nightly for 7 days "\
                           "[stdout]"
                    , type='string'
                    , metavar="FILE"
                     )
logging_group.add_option( "-i", "--log-filter"
                    , action="callback"
                    , callback=store_raw
                    , default=None
                    , dest="log_filter"
                    , help="the subsystem outside of which messages will "\
                           "not be logged []"
                    , type='string'
                    , metavar="FILTER"
                     )
logging_group.add_option( "-t", "--log-format"
                    , action="callback"
                    , callback=store_raw
                    , default=None
                    , dest="log_format"
                    , help="the log message format per the Formatter class "\
                           "in the Python standard library's logging module "\
                           "[%(message)s]"
                    , type='string'
                    , metavar="FORMAT"
                     )
logging_group.add_option( "-v", "--log-level"
                    , action="callback"
                    , callback=callback_log_level
                    , choices=LOG_LEVELS
                    , default=None
                    , help="the importance level at or above which to log "\
                           "a message; options are %s [WARNING]" % \
                           ', '.join(LOG_LEVELS)
                    , type='choice'
                    , metavar="LEVEL"
                     )
optparser.add_option_group(logging_group)



class Paths:
    """Junkdrawer for a few paths we like to keep around.
    """

    def __init__(self, root):
        """Takes the website's filesystem root.

            root    website's filesystem root: /
            __      magic directory: /__
            lib     python library: /__/lib/python{x.y}
            plat    platform-specific python library: /__/lib/plat-<foo>

        If there is no magic directory, then __, lib, and plat are all None. If
        there is, then lib and plat are added to sys.path.

        """
        self.root = root
        self.__ = os.path.join(self.root, '__')
        if not os.path.isdir(self.__):
            self.__ = None
            self.lib = None
            self.plat = None
        else:
            lib = os.path.join(self.__, 'lib', 'python')
            if os.path.isdir(lib):
                self.lib = lib
            else:
                lib = os.path.join(self.__, 'lib', 'python'+sys.version[:3])
                self.lib = os.path.isdir(lib) and lib or None

            plat = os.path.join(lib, 'plat-'+sys.platform)
            self.plat = os.path.isdir(plat) and plat or None

            pkg = os.path.join(lib, 'site-packages')
            self.pkg = os.path.isdir(pkg) and pkg or None

            for path in (lib, plat, pkg):
                if os.path.isdir(path):
                    sys.path.insert(0, path)


class ConfFile(ConfigParser.RawConfigParser):
    """Represent a configuration file.

    This class wraps the standard library's RawConfigParser class. The
    constructor takes the path of a configuration file. If the file does not
    exist, you'll get an empty object. Use either attribute or key access on
    instances of this class to return section dictionaries. If a section doesn't
    exist, you'll get an empty dictionary.

    """

    def __init__(self, filepath=None):
        ConfigParser.RawConfigParser.__init__(self)
        if filepath is not None:
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

    args = None     # argument list as returned by OptionParser.parse_args
    conf = None     # a ConfFile instance
    optparser = None # an optparse.OptionParser instance
    opts = None     # an optparse.Values instance per OptionParser.parse_args
    paths = None    # a Paths instance

    address = None  # the AF_INET, AF_INET6, or AF_UNIX address to bind to
    command = None  # one of restart, start, status, stop; optional []
    daemon = None   # Daemon object or None; whether to daemonize
    defaults = None # tuple of default resource names for a directory
    sockfam = None  # one of socket.AF_{INET,INET6,UNIX}
    threads = None  # the number of threads in the pool


    def __init__(self, argv):
        """Takes an argv list, gives it straight to optparser.parse_args.
        """

        # Initialize parsers.
        # ===================
        # The 'root' knob can only be specified on the command line.

        opts, args = optparser.parse_args(argv)
        paths = Paths(opts.root)                # default handled by optparse
        conf = ConfFile(os.path.join(paths.root, '__', 'etc', 'aspen.conf'))

        self.args = args
        self.conf = conf
        self.optparser = optparser
        self.opts = opts
        self.paths = paths


        # command/daemon
        # ==============
        # Like root, 'command' can only be given on the command line.

        command = ''
        if args:
            command = args[0]
        if command and command not in COMMANDS:
            raise ConfigurationError("Bad command: %s" % command)
        want_daemon = command != ''
        if want_daemon and WINDOWS:
            raise ConfigurationError("Can only daemonize on UNIX.")

        self.command = command
        self.daemon = Daemon(self)


        # address/sockfam & mode
        # ======================
        # These can be set either on the command line or in the conf file.

        if getattr(opts, 'have_address', False):        # first check CLI
            address = opts.address
            sockfam = opts.sockfam
        elif 'address' in conf.main:                    # then check conf
            address, sockfam = validate_address(conf.main['address'])
        else:                                           # default from optparse
            address = opts.address
            sockfam = socket.AF_INET

        if getattr(opts, 'have_mode', False):           # first check CLI
            mode_ = opts.mode
        elif 'mode' in conf.main:                       # then check conf
            mode_ = conf.main['mode']
        else:                                           # default from mode
            mode_ = mode.get()

        self.address = address
        self.sockfam = sockfam
        self._mode = mode_ # mostly for testing
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


        # http_version
        # ------------

        http_version = conf.main.get('http_version', '1.1')
        if http_version not in ('1.0', '1.1'):
            raise TypeError( "http_version must be 1.0 or 1.1, "
                           + "not '%s'" % http_version
                            )
        self.http_version = http_version


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
        # Logging can be configured from four places, in this order of 
        # precedence:
        #
        #   1) some other module (theoretically, I'm not sure an aspen user 
        #      could make this happen easily)
        #   2) the command line
        #   3) a logging.conf file
        #   4) a [logging] section in the aspen.conf file
        #
        # These are not layered; only one is used.

        #FMT = "%(process)-6s%(levelname)-9s%(name)-14s%(message)s"

        logging_configured = bool(len(logging.getLogger().handlers))
                             # this test is taken from logging.basicConfig.

        if logging_configured:              # some other module
            log.warn("logging is already configured")

        if not logging_configured:          # command line
            kw = dict()
            kw['filename'] = opts.log_file
            kw['filter'] = opts.log_filter
            kw['format'] = opts.log_format
            kw['level'] = opts.log_level
            if kw.values() != [None, None, None, None]: # at least one knob set
                if kw['format'] is None:
                    kw['format'] = LOG_FORMAT
                if kw['level'] is None:
                    kw['level'] = LOG_LEVEL
                self.configure_logging(**kw)
                log.info("logging configured from the command line")
                logging_configured = True

        if not logging_configured:          # logging.conf
            logging_conf = os.path.join(paths.root, '__', 'etc', 'logging.conf')
            if os.path.exists(logging_conf):
                logging.config.fileConfig(logging_conf) 
                log.info("logging configured from logging.conf")
                logging_configured = True

        if not logging_configured:          # aspen.conf [logging]
            kw = dict()
            kw['filename'] = conf.logging.get('file')
            kw['filter'] = conf.logging.get('filter')
            kw['format'] = conf.logging.get('format', LOG_FORMAT)

            log_level = conf.logging.get('level')
            if log_level is not None:
                log_level = validate_log_level(log_level) 
            else:
                log_level = LOG_LEVEL
            kw['level'] = log_level

            self.configure_logging(**kw)
            log.info("logging configured from aspen.conf")
            logging_configured = True


        # PIDFile
        # =======
        # Pidfile only gets written in CHILD of a daemon.

        vardir = os.path.join(self.paths.root, '__', 'var')
        pidpath = os.path.join(vardir, 'aspen.pid')
        pidfile = PIDFile(pidpath)
        self.pidfile = pidfile


    def configure_logging(self, filename, filter, format, level):
        """Used for configuring logging from the command line or aspen.conf.
        """
    
        # Handler
        # =======
        # sys.stdout or rotated file
   
        if filename is None:
            handler = StreamHandler(sys.stdout)
        else:
            # @@: Handle absolute paths on Windows
            #  http://sluggo.scrapping.cc/python/unipath/Unipath-current/unipath/abstractpath.py
            #  http://docs.python.org/library/os.path.html#os.path.splitunc
            if not filename.startswith('/'):
                filename = os.path.join(self.paths.root, filename)
                filename = os.path.realpath(filename)
            logdir = os.path.dirname(filename)
            if not os.path.isdir(logdir):
                os.makedirs(logdir, 0755)
            handler = TimedRotatingFileHandler( filename=filename
                                              , when='midnight'
                                              , backupCount=7
                                               )
        # Filter
        # ======
        
        if filter is not None:
            filter = logging.Filter(filter)
            handler.addFilter(filter)
    
    
        # Format
        # ======
   
        formatter = logging.Formatter(fmt=format)
        handler.setFormatter(formatter)


        # Level
        # =====

        handler.setLevel(level)

    
        # Installation
        # ============
   
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(level) # bah

