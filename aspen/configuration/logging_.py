import logging
import logging.config
import sys
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from os.path import dirname, exists, expanduser, isdir, join, realpath

from aspen.configuration.optparser import validate_log_level


LOG_FORMAT = "%(message)s"
LOG_LEVEL = logging.WARNING
log = logging.getLogger('aspen.configuration.logging')


def configure_logging(opts, dotaspen, conf):
    """Given an opts object, configure logging.
    
    Logging can be configured from four places, in this order of 
    precedence:
    
      1) some other module (theoretically, I'm not sure an aspen user 
         could make this happen easily)
      2) the command line
      3) a logging.conf file
      4) a [logging] section in the aspen.conf file
    
    These are not layered; only one is used.

    """

    #FMT = "%(process)-6s%(levelname)-9s%(name)-14s%(message)s"

    kw = None
    logging_configured = bool(len(logging.getLogger().handlers))
                         # this test is taken from logging.basicConfig.

    if logging_configured:              # some other module
        log.warn("Logging is already configured, so aspen won't perform "
                 "any logging configuration.")

    if not logging_configured:          # command line
        kw = {'dotaspen': dotaspen}
        kw['filename'] = opts.log_file
        kw['filter'] = opts.log_filter
        kw['format'] = opts.log_format
        kw['level'] = opts.log_level
        if kw.values() != [None, None, None, None]: # at least one knob set
            if kw['format'] is None:
                kw['format'] = LOG_FORMAT
            if kw['level'] is None:
                kw['level'] = LOG_LEVEL
            simple_logging(**kw)
            log.info("Logging configured from the command line.")
            logging_configured = True

    if not logging_configured:          # logging.conf
        # TODO /etc/aspen/logging.conf
        # TODO /usr/local/etc/aspen/logging.conf
        logging_conf = join(dotaspen, 'logging.conf')
        if exists(logging_conf):
            logging.config.fileConfig(logging_conf) 
            log.info("logging configured from logging.conf")
            logging_configured = True

    if not logging_configured:          # aspen.conf [logging]
        kw = {'dotaspen': dotaspen}
        kw['filename'] = conf.logging.get('file')
        kw['filter'] = conf.logging.get('filter')
        kw['format'] = conf.logging.get('format', LOG_FORMAT)

        log_level = conf.logging.get('level')
        if log_level is not None:
            log_level = validate_log_level(log_level) 
        else:
            log_level = LOG_LEVEL
        kw['level'] = log_level

        simple_logging(**kw)
        log.info("Logging configured from aspen.conf.")
        logging_configured = True

    if kw is not None:
        return kw['filename'], kw['filter'], kw['format'], kw['level']
    else:
        return None, None, None, None


def simple_logging(dotaspen, filename, filter, format, level):
    """Used for configuring logging from the command line or aspen.conf.
    """
    handler = get_handler(dotaspen, filename)
    if filter is not None:
        filter = logging.Filter(filter)
        handler.addFilter(filter)
    formatter = logging.Formatter(fmt=format)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level) # bah

def get_handler(dotaspen, filename):
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
            filename = join(dotaspen, filename)
            filename = realpath(filename)
        logdir = dirname(filename)
        if not isdir(logdir):
            os.makedirs(logdir, 0644)
        handler = TimedRotatingFileHandler( filename=filename
                                          , when='midnight'
                                          , backupCount=7
                                           )
    return handler
