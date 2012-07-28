"""Define parser/validators for configuration system

Each of these is guaranteed to be passed a unicode object as read from the
environment or the command line.

"""
import os
import socket

import aspen
from aspen.utils import typecheck
from aspen.http.response import charset_re


def identity(value):
    typecheck(value, unicode)
    return value

def media_type(media_type):
    # XXX for now. Read a spec
    return media_type.encode('US-ASCII')

def charset(value):
    typecheck(value, unicode)
    if charset_re.match(value) is None:
        raise ValueError("charset not to spec")
    return value

def yes_no(s):
    typecheck(s, unicode)
    s = s.lower()
    if s in [u'yes', u'true', u'1']:
        return True
    if s in [u'no', u'false', u'0']:
        return False
    raise ValueError("must be either yes/true/1 or no/false/0")

def list_(value):
    """Return a tuple of (bool, list).

    The bool indicates whether to extend the existing config with the list, or
    replace it.

    """
    typecheck(value, unicode)
    extend = False
    if value.startswith('+'):
        extend = True
        value = value[1:]
    stripped = [x.strip() for x in value.split(',')]
    seen = set()
    out = []
    for x in stripped:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return (extend, out)

def network_engine(value):
    typecheck(value, unicode)
    if value not in aspen.NETWORK_ENGINES:
        msg = "not one of {%s}" % (','.join(aspen.NETWORK_ENGINES))
        raise ValueError(msg)
    return value

def renderer(value):
    typecheck(value, unicode)
    if value not in aspen.RENDERERS:
        msg = "not one of {%s}" % (','.join(aspen.RENDERERS))
        raise ValueError(msg)
    return value.encode('US-ASCII')

def network_address(address):
    """Given a socket address string, return a tuple (sockfam, address).

    This is called from a couple places, and is a bit complex.

    """
    typecheck(address, unicode)

    if address[0] in (u'/', u'.'):
        if aspen.WINDOWS:
            raise ValueError("can't use an AF_UNIX socket on Windows")
            # but what about named pipes?
        sockfam = socket.AF_UNIX
        # We could test to see if the path exists or is creatable, etc.
        address = os.path.realpath(address)

    elif address.count(u':') > 1:
        sockfam = socket.AF_INET6
        # @@: validate this, eh?

    else:
        sockfam = socket.AF_INET
        # Here we need a tuple: (str, int). The string must be a valid
        # IPv4 address or the empty string, and the int -- the port --
        # must be between 0 and 65535, inclusive.


        # Break out IP and port.
        # ======================

        if address.count(u':') != 1:
            raise ValueError("Wrong number of :'s. Should be exactly 1")
        ip_port = address.split(u':')
        ip, port = [i.strip() for i in ip_port]


        # IP
        # ==

        if ip == u'':
            ip = u'0.0.0.0' # IP defaults to INADDR_ANY for AF_INET; specified
                            # explicitly to avoid accidentally binding to
                            # INADDR_ANY for AF_INET6.
        elif ip == u'localhost':
            ip = u'127.0.0.1'  # special case for nicer user experience
        else:
            try:
                # socket.inet_aton is more permissive than we'd like
                parts = ip.split('.')
                assert len(parts) == 4
                for p in parts:
                    assert p.isdigit()
                    assert 0 <= int(p) <= 255
            except AssertionError:
                raise ValueError("invalid IP")


        # port
        # ====
        # Coerce to int. Must be between 0 and 65535, inclusive.

        try:
            port = int(port)
        except ValueError:
            raise ValueError("invalid port (non-numeric)")

        if not(0 <= port <= 65535):
            raise ValueError("invalid port (out of range)")


        # Success!
        # ========

        address = (ip, port)


    return address, sockfam
