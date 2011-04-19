import os
import sys
from os.path import isfile

import diesel


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


# Startup
# =======

def startup(website):
    # This is not ideal. See http://sync.in/aspen-reloading

    if not website.configuration.conf.aspen.no('changes_kill'):
        return 

    dotaspen = join(configuration.root, '.aspen')
    for root, dirs, files in os.walk(dotaspen):
        for filename in files:
            add(join(root, filename))

    def loop():
        while True:
            check_all()
            diesel.sleep(0.5)
    website.configuration.app.add_loop(diesel.Loop(loop))
