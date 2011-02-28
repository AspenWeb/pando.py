"""Define configuration objects.
"""
import logging
import logging.config
import os
import socket
import sys
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

import aspen
from aspen.configuration.aspenconf import AspenConf 
from aspen.configuration.exceptions import ConfigurationError
from aspen.configuration.hooks import HooksConf
from aspen.configuration.optparser import optparser


log = logging.getLogger('aspen') # configured below; not used until then


LOG_FORMAT = "%(message)s"
LOG_LEVEL = logging.WARNING


class Configuration(object):
    """Aggregate configuration from several sources.
    """

    root = ''       # string, filesystem root
    args = None     # argument list as returned by OptionParser.parse_args
    conf = None     # a AspenConf instance
    optparser = None # an optparse.OptionParser instance
    opts = None     # an optparse.Values instance per OptionParser.parse_args

    address = None  # the AF_INET, AF_INET6, or AF_UNIX address to bind to
    sockfam = None  # one of socket.AF_{INET,INET6,UNIX}


    def __init__(self, argv):
        """Takes an argv list, gives it straight to optparser.parse_args.
        """

        # Initialize parsers.
        # ===================

        opts, args = optparser.parse_args(argv)


        # Root
        # ====
        # This can only be passed on the command line.

        root = os.getcwd()
        if args:
            root = args[0]
        root = os.path.realpath(root)
        if not os.path.isdir(root):
            msg = "%s does not point to a directory" % root
            raise ConfigurationError(msg)


        conf = AspenConf( '/etc/aspen/aspen.conf'
                        , os.path.expanduser('~/.aspen/aspen.conf') 
                        , os.path.join(root, '.aspen', 'etc', 'aspen.conf')
                         ) # later overrides earlier
        
        self.root = root
        self.args = args
        self.conf = conf
        self.optparser = optparser
        self.opts = opts


        # hooks
        # =====

        self.hooks = HooksConf( '/etc/aspen/hooks.conf'
                              , os.path.expanduser('~/.aspen/hooks.conf')
                              , os.path.join(root,'.aspen','etc','hooks.conf')
                               ) # later comes after earlier, per section


        # address/sockfam
        # ===============
        # These can be set either on the command line or in the conf file.

        if getattr(opts, 'have_address', False):        # first check CLI
            address = opts.address
            sockfam = opts.sockfam
        elif 'address' in conf.main:                    # then check conf
            address, sockfam = validate_address(conf.main['address'])
        else:                                           # default from optparse
            address = opts.address
            sockfam = socket.AF_INET

        self.address = address
        self.sockfam = sockfam


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
            logging_conf = os.path.join(root, '__', 'etc', 'logging.conf')
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
