class ConfigurationError(StandardError):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        StandardError.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class ConfFileError(ConfigurationError):

    def __init__(self, msg, filename, lineno):
        msg = "On line %d of %s, %s" % (lineno, filename, msg)
        ConfigurationError.__init__(self, msg)
