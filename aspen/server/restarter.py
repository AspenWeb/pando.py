import logging
import os
import sys
import time
import threading
from os.path import join, isfile


log = logging.getLogger('aspen.restarter')
extras = []
mtimes = {}


def add(filename):
    extras.append(filename)

def check_one(filename):
    """Given a filename, return None or exit.
    """

    # The file may have been removed from the filesystem.
    # ===================================================

    if not isfile(filename):
        if filename in mtimes:
            log.info("file deleted: %s" % filename)
            sys.exit(1) # trigger restart
        else:
            # We haven't seen the file before. It has probably been loaded 
            # from a zip (egg) archive.
            return


    # Or not, in which case, check the mod time.
    # ==========================================

    mtime = os.stat(filename).st_mtime
    if filename not in mtimes: # first time we've seen it
        mtimes[filename] = mtime
    if mtime > mtimes[filename]:
        log.info("file changed: %s" % filename)
        sys.exit(1) # trigger restart

def check_all():
    """See if any of our available modules have changed on the filesystem.
    """
    for name, module in sorted(sys.modules.items()):    # module files
        filepath = getattr(module, '__file__', None)
        if filepath is None:
            # We land here when a module is an attribute of another module
            # i.e., it exists twice in the sys.modules table, once as its
            # canonical representation, and again having been imported
            # within another module.
            continue
        filepath = filepath.endswith(".pyc") and filepath[:-1] or filepath
        check_one(filepath)

    for filepath in extras:                             # additional files
        check_one(filepath)


# Setup
# =====

def install(website):
    """Given a Website instance, start a loop over check_all.
    """
    # This is not ideal. See http://sync.in/aspen-reloading

    if website.dotaspen is not None:
        for root, dirs, files in os.walk(website.dotaspen):
            for filename in files:
                add(join(root, filename))

    website.engine.start_restarter(check_all)
