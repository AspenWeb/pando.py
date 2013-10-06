"""
Exceptions used by Aspen
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class LoadError(Exception):
    """Represent a problem loading a resource.
    """
    # Define this here to avoid import issues when json doesn't exist.


class CRLFInjection(Exception):
    def __str__(self):
        return "Possible CRLF injection detected."
