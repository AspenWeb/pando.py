import os
import logging
import sys
import time
from os.path import join

from aspen.website import Website


log = logging.getLogger('aspen.cli')


def main(argv=None):
    """http://aspen.io/cli/
    """
    try:
        if argv is None:
            argv = sys.argv[1:]
        website = Website(argv)
        try:
            website.serve()
        finally:
            website.shutdown()
    except KeyboardInterrupt, SystemExit:
        pass

def thrash():
    """This is a very simple tool to restart a process when it dies.

    It's designed to restart aspen in development when it dies because files
    have changed and you set changes_kill in the [aspen] section of aspen.conf.

    http://aspen.io/thrash/

    """
    try:
        while 1:
            os.system(' '.join(sys.argv[1:]))
            time.sleep(1)
    except KeyboardInterrupt:
        pass
