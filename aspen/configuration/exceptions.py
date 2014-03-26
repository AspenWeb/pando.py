"""
aspen.configuration.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exceptions used by Aspen's configuration module
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class ConfigurationError(StandardError):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        StandardError.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg
