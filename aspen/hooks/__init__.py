"""Give users some control over the server and request lifecycles.
"""

class Hooks(object):
    """Model a collection of named application extension points.

    >>> hooks = Hooks()
    >>> hooks.point_a = [func1, func2]
    >>> hooks.run('point_a', thing)
    ...

    """

    def run(self, hook_name, thing):
        """Takes an attribute name and a request/response/website.
        """
        for func in getattr(self, hook_name, []):
            thing = func(thing) or thing
        return thing
