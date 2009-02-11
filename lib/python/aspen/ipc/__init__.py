"""This module encapsulates interprocess communication functionality.
"""
import errno
import logging
import os
import signal
import time


log = logging.getLogger('aspen.ipc')


# Fault-tolerant kill
# ===================

def death_watch(is_dead, pid):
    """Given a non-blocking test for deadness and a pid, call it with a timeout.
    """
    timeout = 5 # seconds
    last_attempt = time.time()
    while 1:
        if is_dead(pid):                                # daemon has stopped
            out = True
            break
        elif (last_attempt + timeout) < time.time():    # time's up
            out = False
            break
        else:
            time.sleep(0.2)
    return out

def is_probably_dead(pid):
    """Return a boolean; True means the proc is most likely dead.

    This function is used when the process in question is not a child of ours.

    Reference for this use of kill:

        "The most-used technique is to assume that success or failure with
        EPERM implies that the process exists, and any other error implies that
        it doesn't." 
                     -- http://www.steve.org.uk/Reference/Unix/faq_2.html#SEC18

    Also:

        http://blog.ianbicking.org/daemon-best-practices.html
        http://svn.pythonpaste.org/Paste/Script/tags/1.7.3/paste/script/serve.py
        http://www.mems-exchange.org/software/qp/qp-2.1.tar.gz/qp-2.1/lib/site.py 

    """
    def is_dead(pid):
        try:
            os.kill(pid, 0)
        except OSError, err:
            if err.errno != errno.EPERM:
                return True
        return False
    return death_watch(is_dead, pid)

def is_really_dead(pid):
    """Unlike is_probably_dead above, this function uses os.wait().
    """
    def is_dead(pid):
        pid, status = os.waitpid(pid, os.WNOHANG)
        return os.WIFEXITED(status) or os.WIFSIGNALED(status)
    return death_watch(is_dead, pid)


def kill_nicely(pid, is_our_child):
    """Given a pid, terminate the process; return value indicates compliance.

    If is_our_child is True, then we use os.wait to reap the process. Otherwise
    we use os.kill(pid, 0).

    We send two SIGTERMs and a SIGKILL before quitting. The process gets 5
    seconds after each SIGTERM to shut down.

    """

    is_dead = is_our_child and is_really_dead or is_probably_dead 

    def kill(sig):
        try:
            os.kill(pid, sig)
        except OSError, exc:
            log.error(str(exc))
            raise SystemExit(1)

    kill(signal.SIGTERM)
    if is_dead(pid):
        return True

    log.error("%d still going; resending SIGTERM" % pid)
    kill(signal.SIGTERM)
    if is_dead(pid):
        return True

    log.critical("%d STILL going; sending SIGKILL" % pid)
    kill(signal.SIGKILL)
    if not is_dead(pid):
        msg = "%d STILL GOING FIVE SECONDS AFTER SIGKILL; I give up." % pid
        log.critical(msg)
    return False


# Signal helper
# =============

signum2name = dict()
for signame, signum in signal.__dict__.items():
    if isinstance(signum, int):
        if signame.startswith('SIG') and not signame[3] == '_':
            signum2name[signum] = signame

def get_signame(signum):
    return signum2name[signum]

