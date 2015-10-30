"""
aspen.configuration.parse
~~~~~~~~~~~~~~~~~~~~~~~~~

Define parser/validators for configuration system

Each of these is guaranteed to be passed a unicode object as read from the
environment or the kwargs.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .. import RENDERERS, six
from ..utils import typecheck
from ..http.response import charset_re


def identity(value):
    typecheck(value, six.text_type)
    return value

def media_type(media_type):
    # XXX for now. Read a spec
    return media_type.encode('US-ASCII')

def charset(value):
    typecheck(value, six.text_type)
    if charset_re.match(value) is None:
        raise ValueError("charset not to spec")
    return value

def yes_no(s):
    typecheck(s, six.text_type)
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
    typecheck(value, six.text_type)
    extend = value.startswith('+')
    if extend:
        value = value[1:]

    # populate out with a single copy
    # of each non-empty item, preserving order
    out = []
    for v in value.split(','):
        v = v.strip()
        if v and not v in out:
            out.append(v)

    return (extend, out)

def renderer(value):
    typecheck(value, six.text_type)
    if value not in RENDERERS:
        msg = "not one of {%s}" % (','.join(RENDERERS))
        raise ValueError(msg)
    return value.encode('US-ASCII')
