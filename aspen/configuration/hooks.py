class Hooks:
    """This is a module that safely delegates running a hook to another object.
    """

    def __init__(self, aspen_hooks):
        """Try to import aspen_hooks.
        """
        self.hooks = aspen_hooks

    def run(self, name, thing):
        """Takes a section name and a Request, Response, or Website object
        """
        func = getattr(self.hooks, name, None)
        if func is not None:
            thing = func(thing) or thing
        return thing
