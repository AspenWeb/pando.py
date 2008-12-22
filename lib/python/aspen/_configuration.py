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
import logging.config
import os
import socket
import sys
import optparse
import ConfigParser

from aspen import load, mode


log = logging.getLogger('aspen') # configured below; not used until then
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
        address = os.path.realpath(address)

    elif address.count(':') > 1:
        sockfam = socket.AF_INET6
        # @@: validate this, eh?

    else:
        sockfam = socket.AF_INET
        # Here we need a tuple: (str, int). The string must be a valid
        # IPv4 address or the empty string, and the int -- the port --
        # must be between 0 and 65535, inclusive.


        err = "Bad address %s" % str(address)


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
    parser_.values.have_address = True


def callback_root(option, opt, value, parser_):
    """Expand the root directory path and make sure the directory exists.
    """
    value = os.path.realpath(value)
    if not os.path.isdir(value):
        msg = "%s does not point to a directory" % value
        raise optparse.OptionValueError(msg)
    parser_.values.root = value


def callback_mode(option, opt, value, parser_):
    """Indicate that we have a mode from the command line.
    """
    parser_.values.mode = value
    parser_.values.have_mode= True


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
optparser.add_option( "-m", "--mode"
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
optparser.add_option( "-r", "--root"
                    , action="callback"
                    , callback=callback_root
                    , default=os.getcwd()
                    , dest="root"
                    , help="the root publishing directory [.]"
                    , type='string'
                     )


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
        conf = ConfFile(os.path.join(paths.root, '__', 'etc', 'aspen.conf'))

        self.args = args
        self.conf = conf
        self.optparser = optparser
        self.opts = opts
        self.paths = paths


        # command/daemon
        # ==============
        # Like root, 'command' can only be given on the command line.

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
        # Configured using the standard library's logging.config.fileConfig.
       
        logging_configured = False
        if paths.__ is not None:
            logging_conf = os.path.join(paths.__, 'etc', 'logging.conf')
            if os.path.exists(logging_conf):
                logging.config.fileConfig(logging_conf) 
                log.info("logging configured from file")
                logging_configured = True
        if not logging_configured:
            logging.basicConfig()
            logging.root.setLevel(logging.NOTSET)
            log.info("basic logging configured")


