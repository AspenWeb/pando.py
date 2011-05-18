import os
import sys
import time
from aspen.http.response import Response

try:                # Python 2.6+
    import json
except ImportError: # Python 2.5-
    try:
        import simplejson as json
    except ImportError:
        json = None


__version__ = "~~VERSION~~"
WINDOWS = sys.platform[:3] == 'win'


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
