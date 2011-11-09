import logging
import optparse
import os
import socket
import sys

import aspen
from aspen.configuration.exceptions import ConfigurationError


LOG_LEVELS = ( 'NIRVANA'    # oo
             , 'CRITICAL'   # 50
             , 'ERROR'      # 40
             , 'WARNING'    # 30
             , 'INFO'       # 20
             , 'DEBUG'      # 10
             , 'NOTSET'     #  0
              )


def validate_address(address):
    """Given a socket address string, return a tuple (sockfam, address).

    This is called from a couple places, and is a bit complex.

    """

    if address[0] in ('/','.'):
        if aspen.WINDOWS:
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


usage = "aspen [options] [root]"
version = """\
aspen, version %s

(c) 2006-2011 Chad Whitacre and contributors
http://aspen.io/
""" % aspen.__version__

optparser = optparse.OptionParser(usage=usage, version=version)
optparser.description = """\
Aspen is a Python web framework. By default this program will start serving a
website from the current directory on port 8080. If given arguments the first
will be interpreted as the website root. Options are as follows. See also
http://aspen.io/.
"""


# Basic
# -----

basic_group = optparse.OptionGroup( optparser
                                  , "Basics"
                                  , "How should we get on the network?"
                                   )
basic_group.add_option( "-a", "--address"
                    , action="callback"
                    , callback=callback_address
                    , default=('0.0.0.0', 8080)
                    , dest="address"
                    , help="the IPv4 or Unix address to bind to [0.0.0.0:8080]"
                    , type='string'
                     )
basic_group.add_option( "-e", "--engine"
                    , action="callback"
                    , callback=store_raw
                    , choices=aspen.ENGINES
                    , default=None
                    , dest="engine"
                    , help=( "the HTTP engine to use, one of "
                           + "{%s}" % ','.join(aspen.ENGINES)
                           + " [%s]" % aspen.ENGINES[0]
                            )
                    , type='choice'
                     )

optparser.add_option_group(basic_group)


# Logging 
# -------

logging_group = optparse.OptionGroup( optparser
                                    , "Logging"
                                    , "Configure the Python logging library. "
                                      "For more complex needs use a "
                                      "logging.conf file."
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



