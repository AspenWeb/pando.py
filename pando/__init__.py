from http.cookies import Morsel
from os.path import dirname, join
import sys
import pkg_resources

# imports of convenience
from aspen.simplates import json_ as json
from aspen.simplates.renderers import BUILTIN_RENDERERS, RENDERERS
from .http.response import Response
from .logging import log, log_dammit

# Shut up, flake8. I know I'm addicted to you.
Response, json, log, log_dammit, BUILTIN_RENDERERS, RENDERERS

try:
    dist = pkg_resources.get_distribution('pando')
    __version__ = dist.version
except pkg_resources.DistributionNotFound:
    with open(join(dirname(dirname(__file__)), 'version.txt')) as f:
        __version__ = f.read()

WINDOWS = sys.platform[:3] == 'win'

if sys.version_info < (3, 8, 0):
    # https://stackoverflow.com/q/50813091/2729778
    Morsel._reserved['samesite'] = 'SameSite'
