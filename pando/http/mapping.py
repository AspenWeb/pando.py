"""
:mod:`mapping`
--------------
"""

from aspen.http.mapping import Mapping as _Mapping, NO_DEFAULT


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
        from .response import Response
        raise Response(400, "Missing key: %s" % repr(name))


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
