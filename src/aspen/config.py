import logging
import os
import socket
import sys
import optparse
import ConfigParser
from os.path import join, isdir, realpath

try:
    import pwd
    WINDOWS = False
except:
    WINDOWS = True

from aspen import load, mode


log = logging.getLogger('aspen.config')
COMMANDS = ('start', 'status', 'stop', 'restart', 'runfg')

class ConfigError(StandardError):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        StandardError.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


# Validators
# ==========
# Given a value, return a valid value or raise ConfigError

def validate_address(address):
    """Given a socket address string, return a tuple (sockfam, address)
    """

    if address[0] in ('/','.'):
        if WINDOWS:
            raise ConfigError("Can't use an AF_UNIX socket on Windows.")
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


    return sockfam, address


# Command-Line Option Parser
# ==========================

def cb_address(option, opt, value, parser):
    """Must be a valid AF_INET or AF_UNIX address.
    """
    sockfam, address = validate_address(value)
    parser.values.sockfam = sockfam
    parser.values.address = address


def cb_log_level(option, opt, value, parser):
    """
    """
    try:
        level = getattr(logging, value.upper())
    except AttributeError:
        msg = "Bad log level: %s" % value
        raise optparse.OptionValueError(msg)
    parser.values.log_level = level


def cb_root(option, opt, value, parser):
    """Expand the root directory path and make sure the directory exists.
    """
    value = realpath(value)
    if not isdir(value):
        msg = "%s does not point to a directory" % value
        raise optparse.OptionValueError(msg)
    parser.values.root = value


usage = "aspen [options] [start,stop,&c.]; --help for more"
optparser = optparse.OptionParser(usage=usage)

optparser.add_option( "-a", "--address"
                    , action="callback"
                    , callback=cb_address
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
                    , callback=cb_root
                    , default=os.getcwd()
                    , dest="root"
                    , help="the root publishing directory [.]"
                    , type='string'
                     )
#optparser.add_option( "-v", "--log_level"
#                    , action="callback"
#                    , callback=cb_log_level
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


# Paths
# =====

class Paths:

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


class Configuration(load.Mixin):
    """Aggregate configuration from several sources.

      opts      an optparse.Values instance
      args      a list of command line arguments (no options included)
      paths     a Paths instance (subattrs: root, __, lib, plat)
      fileconf  a RawConfigParser, or None if there is no config file

      command   one of start, stop, restart, runfg (from the command line)


    """

    defaults = ('index.html', 'index.htm', 'index.py')

    def __init__(self, argv):
        """
        """

        # Basics
        # ======

        self.optparser = optparser
        self.opts, self.args = self.optparser.parse_args(argv)
        self.paths = Paths(self.opts.root)

        conf = None
        if self.paths.__ is not None:
            conf = ConfigParser.RawConfigParser()
            conf.read(join(self.paths.__, 'etc', 'aspen.conf'))
        self.conf = conf
        # XXX: validate config file values

        self.environ = dict()
        for k,v in os.environ.items():
            if k.startswith('ASPEN_'):
                self.environ[k[len('ASPEN_'):]] = v
        # XXX: validate envvar values


        # Command
        # =======

        self.command = self.args and self.args[0] or 'runfg'
        if self.command not in COMMANDS:
            raise ConfigError("Bad command: %s" % self.command)
        self.daemon = self.command != 'runfg'
        if self.daemon and sys.platform == 'win32':
            raise ConfigError("Can only daemonize on UNIX.")


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


        # Address
        # =======

        self.address = self.opts.address
        self.sockfam = self.opts.sockfam


        # Mode
        # ====

        mode.set(self.opts.mode)


    def load_plugins(self):
        """Load plugin objects and set on self.

        This adds import/initialization overhead that the parent process doesn't
        need when we are in a restarting situation.

        """
        self.apps = self.load_apps()
        self.handlers = self.load_handlers()
        self.middleware = self.load_middleware()



    # Validators
    # ==========

    #def validate_threads(self, context, candidate):
    #    """Must be an integer greater than or equal to 1.
    #    """
    #
    #    msg = ("Found bad thread count `%s' in context `%s'. " +
    #           "Threads must be an integer greater than or equal to one.")
    #    msg = msg % (str(candidate), context)
    #
    #    if not isinstance(candidate, (int, long)):
    #        isstring = isinstance(candidate, basestring)
    #        if not isstring or not candidate.isdigit():
    #            raise ConfigError(msg)
    #    candidate = int(candidate)
    #    if not candidate >= 1:
    #        raise ConfigError(msg)
    #
    #    return candidate
    #
    #
    #def validate_user(self, context, candidate):
    #    """Must be a valid user account on this system.
    #    """
    #
    #    if WINDOWS:
    #        raise ConfigError("This option is not available on Windows.")
    #
    #    msg = ("Found bad user `%s' in context `%s'. " +
    #           "User must be a valid user account on this system.")
    #    msg = msg % (str(candidate), context)
    #
    #    try:
    #        candidate = pwd.getpwnam(candidate)[2]
    #    except KeyError:
    #        raise ConfigError(msg)
    #
    #    return candidate
