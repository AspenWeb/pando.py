import sys
import pkg_resources

try:                # Python >= 2.6
    from collections import Callable
    def is_callable(obj):
        return isinstance(obj, Callable)
except ImportError: # Python < 2.6
    from operator import isCallable as is_callable

# imports of convenience
from aspen.http.response import Response
from aspen import json_ as json
from aspen.logging import log, log_dammit

# Shut up, PyFlakes. I know I'm addicted to you.
Response, json, is_callable, log, log_dammit

dist = pkg_resources.get_distribution('aspen')
__version__ = dist.version
WINDOWS = sys.platform[:3] == 'win'
NETWORK_ENGINES = ['cheroot', 'cherrypy', 'diesel', 'eventlet', 'gevent',
                   'pants', 'rocket', 'tornado', 'twisted']
RENDERERS = ['jinja2',
            'pystache',
            'tornado',
            'stdlib_format',
            'stdlib_percent',
            'stdlib_template'
            ]
