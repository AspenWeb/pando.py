import math
import codecs
import datetime
import re


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


# datetime helpers
# ================

def total_seconds(td):
    """Python 2.7 adds a total_seconds method to timedelta objects.

    See http://docs.python.org/library/datetime.html#datetime.timedelta.total_seconds

    This function is taken from https://bitbucket.org/jaraco/jaraco.compat/src/e5806e6c1bcb/py26compat/__init__.py#cl-26

    """
    try:
        result = td.total_seconds()
    except AttributeError:
        result = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    return result


class UTC(datetime.tzinfo):
    """UTC - http://docs.python.org/library/datetime.html#tzinfo-objects
    """

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)

utc = UTC()


def utcnow():
    """Return a tz-aware datetime.datetime.
    """
    # For Python < 3, see http://bugs.python.org/issue5094
    return datetime.datetime.now(tz=utc)


def to_age(dt, fmt_past=None, fmt_future=None):
    """Given a timezone-aware datetime object, return an age string.

        range                                       denomination    example
        ======================================================================
        0-1 second                                 "just a moment"
        1-59 seconds                                seconds         13 seconds
        60 sec - 59 min                             minutes         13 minutes
        60 min - 23 hrs, 59 min                     hours           13 hours
        24 hrs - 13 days, 23 hrs, 59 min            days            13 days
        14 days - 27 days, 23 hrs, 59 min           weeks           3 weeks
        28 days - 12 months, 31 days, 23 hrs, 59 mn months          6 months
        1 year -                                    years           1 year

    We'll go up to years for now.

    Times in the future are indicated by "in {age}" and times already passed
    are indicated by "{age} ago". You can pass in custom format strings as
    fmt_past and fmt_future.

    """
    if dt.tzinfo is None:
        raise ValueError("You passed a naive datetime object to to_age.")


    # Define some helpful constants.
    # ==============================

    sec =   1
    min =  60 * sec
    hr  =  60 * min
    day =  24 * hr
    wk  =   7 * day
    mn  =   4 * wk
    yr  = 365 * day


    # Get the raw age in seconds.
    # ===========================

    now = datetime.datetime.now(dt.tzinfo)
    age = total_seconds(abs(now - dt))


    # Convert it to a string.
    # =======================
    # We start with the coarsest unit and filter to the finest. Pluralization
    # is centralized.

    article = "a"

    if age >= yr:           # years
        amount = age / yr
        unit = 'year'
    elif age >= mn:         # months
        amount = age / mn
        unit = 'month'
    elif age >= (2 * wk):   # weeks
        amount = age / wk
        unit = 'week'
    elif age >= day:        # days
        amount = age / day
        unit = 'day'
    elif age >= hr:         # hours
        amount = age / hr
        unit = 'hour'
        article = "an"
    elif age >= min:        # minutes
        amount = age / min
        unit = 'minute'
    elif age >= 1:          # seconds
        amount = age
        unit = 'second'
    else:
        amount = None
        age = 'just a moment'


    # Pluralize, format, and return.
    # ==============================

    if amount is not None:
        amount = int(math.floor(amount))
        if amount != 1:
            unit += 's'
        if amount < 10:
            amount = ['zero', article, 'two', 'three', 'four', 'five', 'six',
                      'seven', 'eight', 'nine'][amount]
        age = ' '.join([str(amount), unit])

    fmt_past = fmt_past if fmt_past is not None else '%(age)s ago'
    fmt_future = fmt_future if fmt_future is not None else 'in %(age)s'
    fmt = fmt_past if dt < now else fmt_future

    return fmt % dict(age=age)


def to_rfc822(dt):
    """Given a datetime.datetime, return an RFC 822-formatted unicode.

        Sun, 06 Nov 1994 08:49:37 -0000

    According to RFC 1123, day and month names must always be in English. If
    not for that, this code could use strftime(). It can't because strftime()
    honors the locale and could generated non-English names.

    """
    tz = ""
    if dt.tzinfo is not None:
        offset = dt.utcoffset()
        if offset is not None:
            sign = "-" if offset.seconds < 0 else "+"
            tz = " " + sign + str(offset.seconds / 60).zfill(4)
    out = dt.strftime("%%s, %d %%s %Y %H:%M:%S") + tz
    days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
              "Oct", "Nov", "Dec")
    out %= (days[dt.weekday()], months[dt.month - 1])
    return out.decode('US-ASCII')


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


# Hostname canonicalization
# =========================

def Canonizer(expected):
    """Takes a netloc such as http://localhost:8080 (no path part).
    """

    def canonize(request):
        """Enforce a certain network location.
        """

        scheme = request.headers.get('X-Forwarded-Proto', 'http') # XXX Heroku
        host = request.headers['Host']  # will 400 if missing

        actual = scheme + "://" + host

        if actual != expected:
            uri = expected
            if request.line.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
                # Redirect to a particular path for idempotent methods.
                uri += request.line.uri.path.raw
                if request.line.uri.querystring:
                    uri += '?' + request.line.uri.querystring.raw
            else:
                # For non-idempotent methods, redirect to homepage.
                uri += '/'
            request.redirect(uri, permanent=True)

    return canonize


if __name__ == '__main__':
    import doctest
    doctest.testmod()
