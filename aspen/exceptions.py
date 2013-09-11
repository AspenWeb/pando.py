"""
Exceptions used by Aspen
"""

class LoadError(Exception):
    """Represent a problem loading a resource.
    """
    # Define this here to avoid import issues when json doesn't exist.


class CRLFInjection(Exception):
    def __str__(self):
        return "Possible CRLF injection detected."
