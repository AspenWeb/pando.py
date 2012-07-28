"""Implement re-execution of the aspen process.

When files change on the filesystem or we receive HUP, we want to re-execute
ourselves.

For thoughts on a more sophisticated approach, see:

    http://sync.in/aspen-reloading

"""
import os
import sys

import aspen


extras = set()
mtimes = {}


###############################################################################
# Thanks, Bob. :) #############################################################
# https://bitbucket.org/cherrypy/magicbus/src/41f5dfb95479/magicbus/wspbus.py #


# Here he saves the value of os.getcwd(), which, if he is imported early
# enough, will be the directory from which the startup script was run. This is
# needed by _do_execv(), to change back to the original directory before
# execv()ing a new process. This is a defense against the application having
# changed the current working directory (which could make sys.executable "not
# found" if sys.executable is a relative-path, and/or cause other problems).
_startup_cwd = os.getcwd()


try:
    import fcntl
except ImportError:
    max_cloexec_files = 0
else:
    try:
        max_cloexec_files = os.sysconf('SC_OPEN_MAX')
    except AttributeError:
        max_cloexec_files = 1024


def _do_execv():
    """Re-execute the current process.

    This must be called from the main thread, because certain platforms
    (OS X) don't allow execv to be called in a child thread very well.

    """
    args = sys.argv[:]
    aspen.log_dammit("Re-executing %s." % ' '.join(args))

    if sys.platform[:4] == 'java':
        from _systemrestart import SystemRestart
        raise SystemRestart
    else:
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]

        os.chdir(_startup_cwd)
        if max_cloexec_files:
            _set_cloexec()
        os.execv(sys.executable, args)


def _set_cloexec():
    """Set the CLOEXEC flag on all open files (except stdin/out/err).

    If self.max_cloexec_files is an integer (the default), then on
    platforms which support it, it represents the max open files setting
    for the operating system. This function will be called just before
    the process is restarted via os.execv() to prevent open files
    from persisting into the new process.

    Set self.max_cloexec_files to 0 to disable this behavior.

    """
    for fd in range(3, max_cloexec_files):  # skip stdin/out/err
        try:
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        except IOError:
            continue
        fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)

#
###############################################################################


execute = _do_execv


def if_changes(filename):
    extras.add(filename)


def check_one(filename):
    """Given a filename, return None or restart.
    """

    # The file may have been removed from the filesystem.
    # ===================================================

    if not os.path.isfile(filename):
        if filename in mtimes:
            aspen.log("File deleted: %s" % filename)
            execute()
        else:
            # We haven't seen the file before. It has probably been loaded
            # from a zip (egg) archive.
            return


    # Or not, in which case, check the modification time.
    # ===================================================

    mtime = os.stat(filename).st_mtime
    if filename not in mtimes: # first time we've seen it
        mtimes[filename] = mtime
    if mtime > mtimes[filename]:
        aspen.log("File changed: %s" % filename)
        execute()


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
    for script_path in website.configuration_scripts:
        if_changes(script_path)
    website.network_engine.start_checking(check_all)
