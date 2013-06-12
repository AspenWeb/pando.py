import sys
import pkg_resources

from backcompat import is_callable

# imports of convenience
from aspen.http.response import Response
from aspen import json_ as json
from aspen.logging import log, log_dammit

# Shut up, PyFlakes. I know I'm addicted to you.
Response, json, is_callable, log, log_dammit

dist = pkg_resources.get_distribution('aspen')
__version__ = dist.version
WINDOWS = sys.platform[:3] == 'win'
NETWORK_ENGINES = ['cheroot']

for entrypoint in pkg_resources.iter_entry_points(group='aspen.network_engines'):
    NETWORK_ENGINES.append(entrypoint.name)

RENDERERS = [ 'stdlib_format'
            , 'stdlib_percent'
            , 'stdlib_template'
            ]

for entrypoint in pkg_resources.iter_entry_points(group='aspen.renderers'):
    RENDERERS.append(entrypoint.name)

RENDERERS.sort()

