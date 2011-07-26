import ConfigParser


YES = set(['1', 'yes', 'true'])
NO = set(['0', 'no', 'false'])
YES_NO = YES | NO


class AspenConfSection(dict):

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
        if name not in self:
            return default 
        val = self[name].lower()
        if val not in YES_NO:
            raise ConfigurationError( "%s should be 'yes' or 'no', not %s" 
                                    % (name, self[name])
                                     )
        return val in YES 


class AspenConf(ConfigParser.RawConfigParser):
    """Represent a configuration file.

    This class wraps the standard library's RawConfigParser class. The
    constructor takes the path of a configuration file. If the file does not
    exist, you'll get an empty object. Use either attribute or key access on
    instances of this class to return section dictionaries. If a section
    doesn't exist, you'll get an empty dictionary.

    """

    def __init__(self, *filenames):
        ConfigParser.RawConfigParser.__init__(self)
        if filenames:
            self.read(filenames)
        self.__sections__ = {}

    def __getitem__(self, name):
        """Given a name, return a dictionary.

        Take care to always return the same dictionary for a given name, so 
        consumers can mutate the dictionary if they want to.

        """
        if name not in self.__sections__:
            section = self.has_section(name) and self.items(name) or []
            section = AspenConfSection(section)
            self.__sections__[name] = section
        return self.__sections__[name]

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.__class__.__dict__:
            return self.__class__.__dict__[name]
        else:
            return self.__getitem__(name)


    # Iteration API
    # =============
    # mostly for testing

    def iterkeys(self):
        return iter(self.sections())
    __iter__ = iterkeys

    def iteritems(self):
        for k in self:
            yield (k, self[k])

    def itervalues(self):
        for k in self:
            yield self[k]



