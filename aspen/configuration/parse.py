"""Define parser/validators for configuration system

Each of these takes a unicode object as read from the environment or the
command line.

"""
import os
import socket

import aspen
from aspen.http.response import charset_re
from aspen.configuration.exceptions import ConfigurationError


def identity(value):
    return value 

media_type = identity  # XXX for now. Read a spec

def charset(value):
    if charset_re.match(value) is None:
        raise ValueError("charset not to spec")
    return value

def yes_no(s):
    s = s.lower()
    if s in [u'yes', u'true', 1]:
        return True
    if s in [u'no', u'false', 0]:
        return False
    raise ValueError("must be either yes/true/1 or no/false/0")

def list_(value):
    """Return a tuple of (bool, list).
    
    The bool indicates whether to extend the existing config with the list, or
    replace it.

    """
    extend = False
    if value.startswith('+'):
        extend = True
        value = value[1:]
    return (extend, list(set([x.strip() for x in value.split(',')])))

def network_engine(value):
    if value not in aspen.ENGINES:
        msg = "not one of {%s}" % (','.join(aspen.ENGINES))
        raise ValueError(msg % value)
    return value

def network_address(address):
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
                if ip == 'localhost':
                    ip = '127.0.0.1'
                else:
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
