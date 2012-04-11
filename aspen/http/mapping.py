NO_DEFAULT = object()


class Mapping(dict):
    """Base class for HTTP mappings: Path, Querystring, Headers, Cookie, Body.

    Mappings in HTTP differ from Python dictionaries in that they may have one
    or more values. This dictionary subclass maintains a list of values for
    each key. Subscript assignment appends to the list, and subscript access
    returns the last item.

    """
  
    def __getitem__(self, name):
        """Given a name, return the last value or raise Response(400).
        """
        try:
            return dict.__getitem__(self, name)[-1]
        except KeyError:
            from aspen import Response
            raise Response(400)

    def __setitem__(self, name, value):
        """Given a name and value, append the value to the list of values.
        """
        if name in self:
            self.all(name).append(value)
        else:
            dict.__setitem__(self, name, [value])

    def pop(self, name, default=NO_DEFAULT):
        """Given a name, return a value.

        This removes the last value from the list for name and returns it. If
        there was only one value in the list then the key is removed from the
        mapping. If name is not present and default is given, that is returned
        instead.

        """
        if name not in self:
            if default is not NO_DEFAULT:
                return default
            else:
                dict.pop(self, name) # KeyError
        values = dict.__getitem__(self, name)
        value = values.pop()
        if not values:
            del self[name]
        return value

    popall = dict.pop

    def all(self, name):
        """Given a name, return a list of values.
        """
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            from aspen import Response
            raise Response(400)
      
    def get(self, name, default=None):
        """Override to only return the last value.
        """
        return dict.get(self, name, [default])[-1]

    def set(self, name, value):
        """Clobber any existing item.
        """
        return dict.__setitem__(self, name, [value])

    def ones(self, *names):
        """Given one or more names of keys, return a list of their values.
        """
        lowered = []
        for name in names:
            n = name.lower()
            if n not in lowered:
                lowered.append(n)
        return [self[name] for name in lowered]


class CaseInsensitiveMapping(Mapping):

    def __init__(self, *a, **kw):
        if a:
            d = a[0]
            items = d.iteritems if hasattr(d, 'iteritems') else d
            for k, v in items():
                self[k] = v
        for k, v in kw.iteritems():
            self[k] = v

    def __getitem__(self, name):
        return Mapping.__getitem__(self, name.title())

    def __setitem__(self, name, value):
        return Mapping.__setitem__(self, name.title(), value)

    def get(self, name, default=None):
        return Mapping.get(self, name.title(), default)

    def set(self, name, value):
        return Mapping.set(self, name.title(), value)

    def all(self, name):
        return Mapping.all(self, name.title())

    def pop(self, name):
        return Mapping.pop(self, name.title())

    def popall(self, name):
        return Mapping.popall(self, name.title())
