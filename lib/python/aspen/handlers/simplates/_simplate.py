class Simplate(object):
    """Base class for framework-specific simplate implementations.

    This class is instantiated on import when each framework is available, and
    is then wired up in handlers.conf.


    Django = Django_0_96

    """

    response_class = None # override w/ framework's response class
                          # used for "raise SystemExit" semantics.

    def __call__(self, environ, start_response):
        """Framework shouldn't override this.
        """

    def build_template(self, template):
        """Given a string, return a framework-specific template object.
        """
        raise NotImplementedError

    def namespace_script(self, namespace):
        """Given a dictionary, populate it with framework objects.
        """
        raise NotImplementedError

    def namespace_template(self, namespace):
        """Given an empty dictionary, populate it with framework objects.

        The result of this call is updated with the result of namespace_script,
        before being used to render the template.

        """
        raise NotImplementedError
