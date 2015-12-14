"""
aspen.utils
+++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import re

import algorithm


# Register a 'repr' error strategy.
# =================================
# Sometimes we want to echo bytestrings back to a user, and we don't know what
# encoding will work. This error strategy replaces non-decodable bytes with
# their Python representation, so that they are human-visible.
#
# See also:
#   - https://github.com/dcrosta/mongo/commit/e1ac732
#   - http://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit

def replace_with_repr(unicode_error):
    offender = unicode_error.object[unicode_error.start:unicode_error.end]
    return (unicode(repr(offender).strip("'").strip('"')), unicode_error.end)

codecs.register_error('repr', replace_with_repr)


def unicode_dammit(s, encoding="UTF-8"):
    """Given a bytestring, return a unicode decoded with `encoding`.

    Any bytes not decodable with UTF-8 will be replaced with their Python
    representation, so you'll get something like u"foo\\xefbar".

    """
    if not isinstance(s, str):
        raise TypeError("I got %s, but I want <type 'str'>." % s.__class__)
    errors = 'repr'
    return s.decode(encoding, errors)


def ascii_dammit(s):
    """Given a bytestring, return a bytestring.

    The returned bytestring will have any non-ASCII bytes replaced with
    their Python representation, so it will be pure ASCII.

    """
    return unicode_dammit(s, encoding="ASCII").encode("ASCII")


# Filters
# =======
# These are decorators for algorithm functions.

def by_lambda(filter_lambda):
    """
    """
    def wrap(function):
        def wrapped_function_by_lambda(*args,**kwargs):
            if filter_lambda():
                return function(*args,**kwargs)
        algorithm._transfer_func_name(wrapped_function_by_lambda, function)
        return wrapped_function_by_lambda
    return wrap


def by_regex(regex_tuples, default=True):
    """Only call function if

    regex_tuples is a list of (regex, filter?) where if the regex matches the
    requested URI, then the flow is applied or not based on if filter? is True
    or False.

    For example:

        from aspen.flows.filter import by_regex

        @by_regex( ( ("/secret/agenda", True), ( "/secret.*", False ) ) )
        def use_public_formatting(request):
            ...

    would call the 'use_public_formatting' flow step only on /secret/agenda
    and any other URLs not starting with /secret.

    """
    regex_res = [ (re.compile(regex), disposition) \
                           for regex, disposition in regex_tuples.iteritems() ]
    def filter_function(function):
        def function_filter(request, *args):
            for regex, disposition in regex_res:
                if regex.matches(request.line.uri):
                    if disposition:
                        return function(*args)
            if default:
                return function(*args)
        algorithm._transfer_func_name(function_filter, function)
        return function_filter
    return filter_function


def by_dict(truthdict, default=True):
    """Filter for hooks

    truthdict is a mapping of URI -> filter? where if the requested URI is a
    key in the dict, then the hook is applied based on the filter? value.

    """
    def filter_function(function):
        def function_filter(request, *args):
            do_hook = truthdict.get(request.line.uri, default)
            if do_hook:
                return function(*args)
        algorithm._transfer_func_name(function_filter, function)
        return function_filter
    return filter_function


# Soft type checking
# ==================

def typecheck(*checks):
    """Assert that arguments are of a certain type.

    Checks is a flattened sequence of objects and target types, like this:

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
    >>> typecheck('foo', unicode)
    Traceback (most recent call last):
        ...
    TypeError: Check #1: 'foo' is of type str, but unicode was expected.
    >>> typecheck('foo', (basestring, None))
    Traceback (most recent call last):
        ...
    TypeError: Check #1: 'foo' is of type str, not one of: basestring, NoneType.
    >>> class Foo(object):
    ...   def __repr__(self):
    ...     return "<Foo>"
    ...
    >>> typecheck(Foo(), dict)
    Traceback (most recent call last):
        ...
    TypeError: Check #1: <Foo> is of type __main__.Foo, but dict was expected.
    >>> class Bar:
    ...   def __repr__(self):
    ...     return "<Bar>"
    ...
    >>> typecheck(Bar(), dict)
    Traceback (most recent call last):
        ...
    TypeError: Check #1: <Bar> is of type instance, but dict was expected.
    >>> typecheck('foo', str, 'bar', unicode)
    Traceback (most recent call last):
        ...
    TypeError: Check #2: 'bar' is of type str, but unicode was expected.

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
