"""Define configuration objects.
"""
import logging
import logging.config
import mimetypes
import os
import socket
import sys
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from os.path import dirname, exists, expanduser, isdir, join, realpath

import aspen
from aspen.configuration.aspenconf import AspenConf 
from aspen.configuration.exceptions import ConfigurationError
from aspen.configuration.hooks import HooksConf
from aspen.configuration.optparser import ( optparser
                                          , validate_address
                                          , validate_log_level
                                           )
from aspen._tornado.template import Loader


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
        """Takes an argv list, and gives it straight to optparser.parse_args.
        """

        # Initialize parsers.
        # ===================

        opts, args = optparser.parse_args(argv)


        # Root
        # ====
        # This can only be passed on the command line.

        if args:
            root = args[0]
        else:
            try:
                # Under supervisord, the following raises 
                #   OSError: [Errno 2] No such file or directory
                # So be sure to pass a directory in on the command line, or cwd
                # using supervisord's own facility for that.
                root = os.getcwd()
            except OSError:
                raise ConfigurationError("Could not get a current working "
                                         "directory. You can specify the site "
                                         "root on the command line.")
        root = realpath(root)
        if not isdir(root):
            msg = "%s does not point to a directory" % root
            raise ConfigurationError(msg)


        # sys.path
        # ========

        dotaspen = join(root, '.aspen')
        if isdir(dotaspen):
            sys.path.insert(0, dotaspen)


        # aspen.conf
        # ==========

        conf = AspenConf( '/etc/aspen/aspen.conf'
                        , '/usr/local/etc/aspen/aspen.conf'
                        , expanduser('~/.aspen/aspen.conf') 
                        , join(dotaspen, 'aspen.conf')
                         ) # later overrides earlier
        
        self.root = root
        self.args = args
        self.conf = conf
        self.optparser = optparser
        self.opts = opts


        # Loader
        # ======

        self.loader = Loader(dotaspen)


        # mimetypes
        # =========
        
        mimetypes.knownfiles = [ join(dirname(__file__), 'mime.types')
                               , '/etc/mime.types'
                               , '/usr/local/etc/mime.types'
                               , join(dotaspen, 'mime.types')
                                ]
        mimetypes.init()

        self.default_mimetype = conf.aspen.get( 'default_mimetype'
                                              , 'text/plain'
                                               )

        # index.html
        # ==========

        default_filenames = conf.aspen.get('default_filenames', 'index.html')
        default_filenames = default_filenames.split()
        default_filenames = [x.strip(',') for x in default_filenames]
        default_filenames = [x for x in default_filenames if x]
        default_filenames = [x.split(',') for x in default_filenames]
        self.default_filenames = []
        for nested in default_filenames:
            self.default_filenames.extend(nested)

       
        # hooks
        # =====

        self.hooks = HooksConf( join(dirname(__file__), 'hooks.conf')
                              , '/etc/aspen/hooks.conf'
                              , '/usr/local/etc/aspen/hooks.conf'
                              , expanduser('~/.aspen/hooks.conf')
                              , join(dotaspen, 'hooks.conf')
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
            # TODO /etc/aspen/logging.conf
            # TODO /usr/local/etc/aspen/logging.conf
            logging_conf = join(root, '.aspen', 'logging.conf')
            if exists(logging_conf):
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
                filename = join(self.paths.root, filename)
                filename = realpath(filename)
            logdir = dirname(filename)
            if not isdir(logdir):
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
