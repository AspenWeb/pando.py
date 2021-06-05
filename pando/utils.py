"""
:mod:`utils`
============
"""

from datetime import datetime, timezone
import re
import string
from urllib.parse import quote


# encoding helpers
# ================

def maybe_encode(s, codec='ascii'):
    return s.encode(codec) if isinstance(s, str) else s


def encode_url(url):
    return maybe_encode(quote(url, string.punctuation))


# datetime helpers
# ================

utc = timezone.utc


def utcnow():
    return datetime.now(tz=utc)


def to_rfc822(dt):
    """Given a datetime.datetime, return an RFC 822-formatted unicode.

        Sun, 06 Nov 1994 08:49:37 GMT

    According to RFC 1123, day and month names must always be in English. If
    not for that, this code could use strftime(). It can't because strftime()
    honors the locale and could generated non-English names.

    """
    t = dt.utctimetuple()
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
        ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[t[6]],
        t[2],
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[t[1] - 1],
        t[0], t[3], t[4], t[5]
    )


# Soft type checking
# ==================

def typecheck(*checks):
    """Assert that arguments are of a certain type.

    Checks is a flattened sequence of objects and target types, like this::

        ( {'foo': 2}, dict
        , [1,2,3], list
        , 4, int
        , True, bool
        , 'foo', (basestring, None)
         )

    The target type can be a single type or a tuple of types. None is
    special-cased (you can specify None and it will be interpreted as
    type(None)).

    >>> typecheck()
    >>> typecheck('foo')
    Traceback (most recent call last):
        ...
    AssertionError: typecheck takes an even number of arguments.
    >>> typecheck({'foo': 2}, dict)
    >>> typecheck([1,2,3], list)
    >>> typecheck(4, int)
    >>> typecheck(True, bool)
    >>> typecheck('foo', (str, None))
    >>> typecheck(None, None)
    >>> typecheck(None, type(None))
    >>> typecheck(b'foo', str)
    Traceback (most recent call last):
        ...
    TypeError: Check #1: b'foo' is of type bytes, but str was expected.
    >>> typecheck('foo', (bytes, None))
    Traceback (most recent call last):
        ...
    TypeError: Check #1: 'foo' is of type str, not one of: bytes, NoneType.
    >>> class Foo:
    ...   def __repr__(self):
    ...     return "<Foo>"
    ...
    >>> typecheck(Foo(), dict)
    Traceback (most recent call last):
        ...
    TypeError: Check #1: <Foo> is of type pando.utils.Foo, but dict was expected.
    >>> typecheck('foo', str, 'bar', int)
    Traceback (most recent call last):
        ...
    TypeError: Check #2: 'bar' is of type str, but int was expected.

    """
    assert type(checks) is tuple, checks
    assert len(checks) % 2 == 0, "typecheck takes an even number of arguments."

    def nice(t):
        found = re.findall("<type '(.+)'>", str(t))
        if found:
            out = found[0]
        else:
            found = re.findall("<class '(.+)'>", str(t))
            if found:
                out = found[0]
            else:
                out = str(t)
        return out

    checks = list(checks)
    checks.reverse()

    nchecks = 0
    while checks:
        nchecks += 1
        obj = checks.pop()
        expected = checks.pop()
        actual = type(obj)

        if isinstance(expected, tuple):
            expected = list(expected)
        elif not isinstance(expected, list):
            expected = [expected]

        for i, t in enumerate(expected):
            if t is None:
                expected[i] = type(t)

        if actual not in expected:
            msg = "Check #%d: %s is of type %s, "
            msg %= (nchecks, repr(obj), nice(actual))
            if len(expected) > 1:
                niced = [nice(t) for t in expected]
                msg += ("not one of: %s." % ', '.join(niced))
            else:
                msg += "but %s was expected." % nice(expected[0])
            raise TypeError(msg)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
