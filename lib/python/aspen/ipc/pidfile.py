"""Manage a pidfile.

We've got PIDFile (object), pidfile (file), and pid (int).

Assuming PIDFile (object) is configured properly, there are three states:

    normal      there is a pidfile with a good pid in it
    stale       there is no pidfile, or there is a pidfile with an old pid
    error       there is a mangled or restricted pidfile

Stale state can be indicated by pid or pidfile conditions, as can error state.
We model this with a series of Exceptions with two base classes each.

"""
import os
import stat
import subprocess
import sys
import time

from aspen.ipc import log


# Exceptions
# ==========

class PIDFilePathNotSet(StandardError):
    """PIDFile (object) is not configured properly.
    """


class State(Exception):     pass
class StaleState(State):    pass
class ErrorState(State):    pass


class PIDFileError(StandardError):
    def __init__(self, pidfile):
        Exception.__init__(self)
        self.pidfile = pidfile.replace(os.getcwd(), '.')
    def __str__(self):
        return "pidfile %s is %s" % (self.pidfile, self.desc)

class PIDFileMissing(PIDFileError, StaleState):
    desc = "missing (is aspen running?)"
class PIDFileRestricted(PIDFileError, ErrorState):
    desc = "restricted (%s)" # instantiate and update this before raising
class PIDFileEmpty(PIDFileError, ErrorState):
    desc = "empty"
class PIDFileMangled(PIDFileError, ErrorState):
    desc = "mangled (%s)" # instantiate and update this before raising


class PIDError(StandardError):
    def __init__(self, pidfile, pid):
        Exception.__init__(self)
        self.pidfile = pidfile
        self.pid = pid
    def __str__(self):
        return "pidfile %s contains %s" % (self.pidfile, self.desc % self.pid)

class PIDDead(PIDError, StaleState):
    desc = "a dead pid (%d)"
class PIDNotAspen(PIDError, StaleState):
    desc = "the pid of a non-aspen process (%s)"


class PIDFile(object):
    """Model a pidfile.
    """

    ASPEN = 'aspen' # factored out to ease testing
    path = None     # path to the pidfile; set before using this object!
    mode = 0644     # the permission bits on the pidfile
    dirmode = 0755  # the permission bits on any directories created

    def __init__(self, path):
        self.path = path

    def write(self):
        pid = os.getpid()
        log.debug("writing pid %d to pidfile %s" % (pid, self.path))
        piddir = os.path.dirname(self.path)
        if not os.path.isdir(piddir):
            os.makedirs(piddir, self.dirmode)
        fp = open(self.path, 'w+')
        self.setperms()
        fp.truncate(0) # CAUSE, YA KNOW, SOMEONE COULD WRITE A BOGUS PID HERE
        fp.write(str(pid))
        fp.close()

    def setperms(self):
        perms = str(oct(self.mode))
        log.debug("setting perms on pidfile %s to %s" % (self.path, perms))
        os.chmod(self.path, self.mode)

    def remove(self):
        if os.path.exists(self.path):
            log.debug("removing pidfile %s" % self.path)
            os.remove(self.path)

    def getpid(self):
        """Return the PID in the pidfile at self.path as an int.

        This is designed to be called by aspen as a daemon driver.

        Possible errors:

            PIDFilePathNotSet   self.path is not set
            PIDFileMissing      the pidfile is missing
            PIDFileRestricted   the user can't read the pidfile
            PIDFileEmpty        the pidfile is empty
            PIDFileMangled      the pidfile is mangled
            PIDDead             the pid does not point to a live process
            PIDNotAspen         the pid does not point to an aspen process

        """
   
        if self.path is None:
            raise PIDFilePathNotSet

        if not os.path.isfile(self.path):
            raise PIDFileMissing(self.path)
        if not os.access(self.path, os.R_OK):
            exc = PIDFileRestricted(self.path)
            perms = str(oct(os.stat(self.path)[stat.ST_MODE] & 0777))
                  # http://www.faqts.com/knowledge_base/view.phtml/aid/5707
            exc.desc = exc.desc % perms
            raise exc

        pid = open(self.path).read() # don't strip(); whitespace is an error
        if not pid:
            raise PIDFileEmpty(self.path)
        if not pid.isdigit():
            exc = PIDFileMangled(self.path)
            exc.desc = exc.desc % pid
            raise exc

        pid = int(pid)
        ps = subprocess.Popen( ["ps", "p%s" % pid, "ww"] # portable?! verified
                             , stdout=subprocess.PIPE    # on FreeBSD and CentOS
                              )
        ps = ps.communicate()[0]
        nlines = ps.count('\n')
        assert nlines in (1,2), "bad input from `ps p%s': %s" % (pid, ps)
        if nlines == 1:                                 # not running
            #  PID  TT  STAT      TIME COMMAND
            raise PIDDead(self.path, pid)
        if nlines == 2:                                 # running
            #  PID  TT  STAT      TIME COMMAND
            #  45489  ??  S      0:02.42 /usr/local/bin/python /usr/local/bi...
            if self.ASPEN is not None: # make allowances for testing
                if self.ASPEN not in ps: # rough approximation
                    log.debug("%s not in %s" % (self.ASPEN, ps))
                    raise PIDNotAspen(self.path, pid)

        return pid

