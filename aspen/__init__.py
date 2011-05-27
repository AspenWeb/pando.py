import os
import sys
import time
from aspen.http.response import Response


# Find a json module.
# ===================
# The standard library includes simplejson as json since 2.6, but without the 
# C speedups. So we prefer simplejson if it is available.

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        json = None


__version__ = "~~VERSION~~"
WINDOWS = sys.platform[:3] == 'win'
ENGINES = ['cherrypy', 'diesel', 'eventlet', 'pants', 'rocket']


def thrash():
    """This is a very simple tool to restart a process when it dies.

    It's designed to restart aspen in development when it dies because files
    have changed and you set changes_kill to 'yes' in the [aspen.cli] section
    of aspen.conf.

    http://aspen.io/thrash/

    """
    try:
        while 1:
            os.system(' '.join(sys.argv[1:]))
            time.sleep(1)
    except KeyboardInterrupt:
        pass
