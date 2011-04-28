from aspen.http import Response

try:                # Python 2.6+
    import json
except ImportError: # Python 2.5-
    try:
        import simplejson as json
    except ImportError:
        json = None


__version__ = "~~VERSION~~"
