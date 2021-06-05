"""
:mod:`mapping`
--------------
"""

from datetime import date
import re

from aspen.http.mapping import Mapping as _Mapping, NO_DEFAULT

from .response import Response


FALSEISH = {'0', 'f', 'false', 'n', 'no'}
"The set of strings that should be converted to :obj:`False`."
TRUEISH = {'1', 't', 'true', 'y', 'yes'}
"The set of strings that should be converted to :obj:`True`."
NULLISH = {'', 'null', 'none'}
"The set of strings that should be converted to :obj:`None`."


class Mapping(_Mapping):

    def __init__(self, *a, **kw):
        """Initializes the mapping.

        Loops through positional arguments first, then through keyword args.

        Positional arguments can be dicts or lists of items.
        """
        for it in a:
            if it is None:
                continue
            items = it.items() if hasattr(it, 'items') else it
            for k, v in items:
                self[k] = v
        for k, v in kw.items():
            self[k] = v

    def keyerror(self, name):
        """Raises a 400 :class:`~pando.http.response.Response`.
        """
        raise Response(400, "Missing key: %s" % repr(name))

    def bool(self, k, default=NO_DEFAULT):
        """Get the last value with key `k`, as a boolean.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value isn't in either the :obj:`.FALSEISH` or :obj:`.TRUEISH` set

        Examples:

        >>> Mapping({'x': 'yes'}).bool('x')
        True
        >>> Mapping({'x': 'False'}).bool('x')
        False
        >>> Mapping({'x': ''}).bool('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value '' is invalid

        """
        try:
            r = self[k].lower()
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        if r in TRUEISH:
            return True
        if r in FALSEISH:
            return False
        raise Response().error(400, "`%s` value %r is invalid" % (k, r))

    def choice(self, k, choices, default=NO_DEFAULT):
        """
        Get the last value with key `k`, and check that it matches one of the
        elements of the `choices` set.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value isn't contained in `choices`

        Examples:

        >>> choices = {'foo'}
        >>> Mapping({'x': 'foo'}).choice('x', choices)
        'foo'
        >>> Mapping({'x': 'Foo'}).choice('x', choices)
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value 'Foo' is invalid. Choices: {'foo'}

        """
        try:
            r = self[k]
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        if r not in choices:
            raise Response().error(400, "`%s` value %r is invalid. Choices: %r" % (k, r, choices))
        return r

    def date(self, k, default=NO_DEFAULT, sep='-'):
        """Get the last value with key `k`, as a :class:`~datetime.date`.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - parsing the value as a date fails

        Examples:

        >>> Mapping({'x': '2021-06-14'}).date('x')
        datetime.date(2021, 6, 14)
        >>> Mapping({'x': '0'}).date('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value '0' is invalid

        """
        try:
            r = self[k]
            if r:
                r = r.split(sep)
            elif default is not NO_DEFAULT:
                return default
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        try:
            year, month, day = map(int, r)
            # the above raises ValueError if the number of parts isn't 3
            # or if any part isn't an integer
            r = date(year, month, day)
        except (ValueError, TypeError):
            raise Response().error(400, "`%s` value %r is invalid" % (k, self[k]))
        return r

    def int(self, k, default=NO_DEFAULT, minimum=None, maximum=None):
        """Get the last value with key `k`, as an integer.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value is greater than `minimum` or lesser than `maximum`

        Examples:

        >>> Mapping({'x': '1'}).int('x')
        1
        >>> Mapping({'x': 'a'}).int('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value 'a' is not a valid integer
        >>> Mapping({'x': '3'}).int('x', maximum=2)
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value 3 is greater than 2
        >>> Mapping({'x': '-1'}).int('x', minimum=0)
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value -1 is less than 0

        """
        try:
            r = self[k]
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        try:
            r = int(r)
        except (ValueError, TypeError):
            raise Response().error(400, "`%s` value %r is not a valid integer" % (k, r))
        if minimum is not None and r < minimum:
            raise Response().error(400, "`%s` value %r is less than %i" % (k, r, minimum))
        if maximum is not None and r > maximum:
            raise Response().error(400, "`%s` value %r is greater than %i" % (k, r, maximum))
        return r

    def list_of(self, cast, k, default=NO_DEFAULT, sep=','):
        """Get the last value with key `k`, split it on `sep`, and `cast()` each substring.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - a call to `cast` raises a :exc:`ValueError`

        Example:

        >>> Mapping({'x': '1,2,3,5,7'}).list_of(int, 'x')
        [1, 2, 3, 5, 7]

        """
        try:
            r = self[k].split(sep)
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        try:
            r = [cast(v) for v in r]
        except ValueError:
            raise Response().error(400, "`%s` value %r is invalid" % (k, self[k]))
        return r

    def match(self, k, pattern, default=NO_DEFAULT):
        r"""Get the last value with key `k`, and check that it matches `pattern`.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value doesn't match the pattern (i.e. ``re.match(pattern, value)``
          returns :obj:`None`)

        Examples:

        >>> pattern = r'^\w+(:\w*)?$'
        >>> Mapping({'x': 'foo'}).match('x', pattern)
        'foo'
        >>> Mapping({'x': '!'}).match('x', pattern)
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value '!' doesn't match the expected pattern

        """
        try:
            v = self[k]
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        if re.match(pattern, v):
            return v
        raise Response().error(400, "`%s` value %r doesn't match the expected pattern" % (k, v))

    def ternary(self, k, default=NO_DEFAULT):
        """Get the last value with key `k`, as a boolean or :obj:`None`.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value isn't in any of :obj:`.FALSEISH`, :obj:`.TRUEISH` or :obj:`.NULLISH`

        Examples:

        >>> Mapping({'x': 'TRUE'}).ternary('x')
        True
        >>> Mapping({'x': 'f'}).ternary('x')
        False
        >>> print(Mapping({'x': ''}).ternary('x'))
        None
        >>> Mapping({'x': 'oui'}).ternary('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value 'oui' is invalid

        """
        try:
            r = self[k].lower()
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        if r in TRUEISH:
            return True
        if r in FALSEISH:
            return False
        if r in NULLISH:
            return None
        raise Response().error(400, "`%s` value %r is invalid" % (k, r))

    def word(self, k, default=NO_DEFAULT, pattern=r'^\w+$', ascii_only=True):
        """Get the last value with key `k`, and check that it matches `pattern`.

        The `ascii_only` argument determines whether the :obj:`re.ASCII` flag is
        passed to :func:`re.match()`.

        Raises a 400 :class:`.Response` if:

        - the key isn't found and no `default` value was provided; or
        - the value doesn't match the pattern (i.e. ``re.match(pattern, value, flag)``
          returns :obj:`None`)

        Examples:

        >>> Mapping({'x': 'foo'}).word('x')
        'foo'
        >>> Mapping({'x': ''}).word('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value '' is empty
        >>> Mapping({'x': 'blé'}).word('x')
        Traceback (most recent call last):
          ...
        pando.http.response.Response: 400 Bad Request: `x` value 'blé' contains forbidden characters
        >>> Mapping({'x': 'blé'}).word('x', ascii_only=False)
        'blé'

        """
        try:
            r = self[k]
        except (KeyError, Response):
            if default is NO_DEFAULT:
                raise
            return default
        if not r:
            raise Response().error(400, "`%s` value %r is empty" % (k, r))
        if not re.match(pattern, r, re.ASCII if ascii_only else 0):
            raise Response().error(400, "`%s` value %r contains forbidden characters" % (k, r))
        return r


class CaseInsensitiveMapping(Mapping):

    def __contains__(self, name):
        return super().__contains__(name.title())

    def __getitem__(self, name):
        return super().__getitem__(name.title())

    def __setitem__(self, name, value):
        return super().__setitem__(name.title(), value)

    def add(self, name, value):
        return super().add(name.title(), value)

    def get(self, name, default=None):
        return super().get(name.title(), default)

    def all(self, name):
        return super().all(name.title())

    def pop(self, name, default=NO_DEFAULT):
        return super().pop(name.title(), default)

    def popall(self, name):
        return super().popall(name.title())


class BytesMapping(Mapping):
    """This mapping automatically transcodes keys and values.

    Attributes:
        encoding (str): UTF-8 by default
        encoding_errors (str): 'backslashreplace' by default

    >>> m = BytesMapping()
    >>> m[b'foo'] = b'bar'
    >>> m[b'foo']
    b'bar'
    >>> m['foo']
    'bar'
    """

    __slots__ = ('encoding', 'encoding_errors')

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.encoding = 'utf8'
        self.encoding_errors = 'backslashreplace'

    def __contains__(self, name):
        if isinstance(name, str):
            name = name.encode(self.encoding, self.encoding_errors)
        return super().__contains__(name)

    def __getitem__(self, name):
        if isinstance(name, str):
            v = super().__getitem__(name.encode(self.encoding, self.encoding_errors))
            if isinstance(v, bytes):
                v = v.decode(self.encoding, self.encoding_errors)
            return v
        else:
            return super().__getitem__(name)

    def __setitem__(self, name, value):
        if isinstance(name, str):
            name = name.encode(self.encoding, self.encoding_errors)
        if isinstance(value, str):
            value = value.encode(self.encoding, self.encoding_errors)
        return super().__setitem__(name, value)

    def add(self, name, value):
        if isinstance(name, str):
            name = name.encode(self.encoding, self.encoding_errors)
        if isinstance(value, str):
            value = value.encode(self.encoding, self.encoding_errors)
        return super().add(name, value)

    def get(self, name, default=None):
        if isinstance(name, str):
            v = super().get(name.encode(self.encoding, self.encoding_errors), default)
            if isinstance(v, bytes):
                v = v.decode(self.encoding, self.encoding_errors)
            return v
        else:
            return super().get(name, default)

    def all(self, name):
        if isinstance(name, str):
            r = super().all(name.encode(self.encoding, self.encoding_errors))
            for i, value in enumerate(r):
                if isinstance(value, bytes):
                    r[i] = value.decode(self.encoding, self.encoding_errors)
            return r
        else:
            return super().all(name)

    def pop(self, name, default=NO_DEFAULT):
        if isinstance(name, str):
            v = super().pop(name.encode(self.encoding, self.encoding_errors), default)
            if isinstance(v, bytes):
                v = v.decode(self.encoding, self.encoding_errors)
            return v
        else:
            return super().pop(name, default)

    def popall(self, name, *default):
        if isinstance(name, str):
            r = super().popall(name.encode(self.encoding, self.encoding_errors), *default)
            for i, value in enumerate(r):
                if isinstance(value, bytes):
                    r[i] = value.decode(self.encoding, self.encoding_errors)
            return r
        else:
            return super().popall(name, *default)
