from aspen.http import Response

try:                # Python 2.6+
    import json
except ImportError: # Python 2.5-
    import simplejson as json


__version__ = "~~VERSION~~"
