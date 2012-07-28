"""Give users some control over the server and request lifecycles.
"""
from aspen import is_callable


class Hooks(dict):
    """Model a collection of application extension points.

    I want attribute access, but dict.__repr__ and __eq__.

    """

    def __init__(self, names):
        """Takes a list of hook names.
        """
        if isinstance(names, basestring):
            raise TypeError("Please pass in an iterable of unicodes.")
        self.__names = names
        for name in names:
            hook = Hook()
            try:
                setattr(self, name, hook)
            except NameError:
                raise ValueError("Hooks names must be valid Python attribute "
                                 "names.")
            dict.__setitem__(self, name, hook)

    def __getitem__(self, name):
        raise NotImplementedError("Please use attribute access.")

    def __setitem__(self, name, value):
        raise NotImplementedError("Please use attribute access.")


class Hook(list):
    """Model a single point where callbacks can be registered.
    """

    def append(self, obj):
        raise NotImplementedError("Please use register.")

    def register(self, obj):
        """Extend to ensure that obj is callable. Could check signature, too.
        """
        if not is_callable(obj):
            raise TypeError("Hooks must be callable objects; this isn't: %s."
                            % str(obj))
        list.append(self, obj)

    def run(self, thing):
        """Takes a request/response/website.
        """
        for hook in self:
            thing = hook(thing) or thing
        return thing
