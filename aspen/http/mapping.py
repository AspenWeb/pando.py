class Mapping(object):
    """Base class for HTTP mappings.

    HTTP forms and headers may have a single item or a list of items as the
    value. So while Python dictionary semantics work for almost everything, it
    is better (IMO) for the API to force you to be explicit about whether you
    are expecting a single item or list of items. We do that here by providing
    'one' and 'all' methods, rather than item access and a 'get' method.
    Furthermore, this class supports iteration over keys, but not iteration
    over values. Iterate over keys, and then use one or all.

    All API here operates on a self._dict dictionary. Set that in subclass
    constructors.

    """

    def __init__(self, **kw):
        self._dict = {}
        for name, value in kw.iteritems():
            self.set(name, value)

    def add(self, name, value):
        """Given a name and value, add another entry.
        """
        if name not in self._dict:
            self.set(name, value)
        else:
            self._dict[name].append(value)

    def __contains__(self, name):
        return name in self._dict

    def all(self, name, default=None):
        """Given a name, return a list of values.
        """
        if default is None:
            default = []
        return self._dict.get(name, default)
       
    def one(self, name, default=None):
        return self._dict.get(name, [default])[0]

    def ones(self, *names):
        """Given one or more names of keys, return a list of their values.
        """
        return [self.one(name) for name in names]

    def __iter__(self):
        return self._dict

    def __in__(self, name):
        """Given a name, return True if it is known in the mapping.
        """
        return name in self._dict

    def __iter__(self):
        return self._dict.__iter__()

    def keys(self):
        """Return a list of names.
        """
        return self._dict.keys()

    def set(self, name, value):
        """Given a name and value, set the value, clearing all others.
        
        Pass None to remove.

        """
        if value is None:
            del self._dict[name]
        self._dict[name] = [str(value).strip()] # TODO unicode?


    # Convenience methods for coercing to bool.
    # =========================================

    def yes(self, name):
        """Given a key name, return a boolean.
        
        The value for the key must be in the set {0,1,yes,no,true,false},
        case-insensistive. If the key is not in this section, we return True.

        """
        return self._yes_no(name, True)

    def no(self, name):
        """Given a key name, return a boolean.
        
        The value for the key must be in the set {0,1,yes,no,true,false},
        case-insensistive. If the key is not in this section, we return False.

        """
        return self._yes_no(name, False)

    def _yes_no(self, name, default):
        if name not in self._dict:
            return default 
        value = self._dict[name].lower()
        if value not in YES_NO:
            raise ConfigurationError( "%s should be 'yes' or 'no', not %s" 
                                    % (name, self._dict[name])
                                     )
        return value in YES 


