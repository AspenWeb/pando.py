import errno
import logging
import os
import sys
import time
import urllib


# Logging
# =======
# We keep one root log handler around during testing, it logs unbuffered to 
# stdout. By default for all tests it only outputs messages filtered with 
# 'aspen.tests'; you can use the `log' logger for that.
#
# If your test needs to check log output from another subsystem, call the 
# filter() method during setup. All logging is reset on teardown.

TEST_SUBSYSTEM = 'aspen.tests'
LOG = os.path.realpath('log')

def set_log_filter(filter):
    """Change the logging subsystem filter.
    """
    root = logging.getLogger()
    handler = root.handlers[0]
    filter = logging.Filter(filter)
    handler.filters = [filter]

def reset_log_filter():
    root = logging.getLogger()
    handler = root.handlers[0]
    for filter in handler.filters:
        handler.removeFilter(filter)
    set_log_filter(TEST_SUBSYSTEM)


def set_log_format(format):
    """Change the logging format.
    """
    root = logging.getLogger()
    handler = root.handlers[0]
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)

def reset_log_format():
    set_log_format("%(message)s")


log = logging.getLogger(TEST_SUBSYSTEM)


class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        logging.StreamHandler.emit(self, record)
        self.flush()

def configure_logging():
    """Using the logging subsystem, send messages from 'aspen.tests' to ./log.
    """
#    logging.raiseExceptions = False
#    logging.shutdown() # @@: triggers
#    logging.raiseExceptions = True 

    fp = open(LOG, 'a') # log is truncated in teardown func in fsfix.py
    handler = FlushingStreamHandler(fp)
    handler.setLevel(0)     # everything

    root = logging.getLogger()
    root.setLevel(0) # everything, still
    root.handlers = [handler]

    set_log_filter(TEST_SUBSYSTEM)

configure_logging()


# Asserters
# =========
# The first two are useful if you want a test generator.

def assert_(expr):
    assert expr

def assert_actual(expected, actual):
    assert actual == expected, actual

def assert_logs(*lines, **kw):
    if lines[0] is None:
        expected = ''
    else:
        # when logged output is printed, system-specific newlines are used
        # when logged output is written to a file, universal newline support 
        #  kicks in, and we have to work around it here
        force_unix_EOL = kw.get('force_unix_EOL', False)
        linesep = force_unix_EOL and '\n' or os.linesep
        expected = linesep.join(lines) + linesep
    actual = kw.get('actual', open(LOG, 'r').read())
    assert actual == expected, actual.splitlines()

def assert_prints(*args):
    args = list(args)
    expected = args[:-1]
    actual = args[-1]
    assert_logs(*expected, **{'actual':actual}) # a little goofy, yes

def assert_raises(Exc, call, *arg, **kw):
    """Given an Exception, a callable, and its params, return an exception.
    """
    exc = None
    try:
        call(*arg, **kw)
    except (SystemExit, Exception), exc: # SystemExit isn't an Exception?!
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (repr(exc), repr(Exc))
    return exc


# IPC helper 
# ==========
# Refs, e.g.:
#
#  http://www.velocityreviews.com/forums/t362297-python-open-a-named-pipe-hanging.html
#  http://coding.derkeiler.com/Archive/Python/comp.lang.python/2004-07/1834.html

NAMED_PIPE = os.path.realpath(os.path.join('fsfix', 'fifo'))
named_pipe_logger = logging.getLogger('OFF-aspen.tests') # twiddle for logging

class TestListener(object):

    def __init__(self):
        named_pipe_logger.info("making named pipe at %s" % NAMED_PIPE)
        fifo = os.mkfifo(NAMED_PIPE)
        self.fifo = open(NAMED_PIPE, 'r')

    def listen_actively(self):
        while 1:
            s = self.fifo.readline().strip()
            if s == 'q':
                named_pipe_logger.info("done listening")
                raise SystemExit
            log.info(s)


class TestTalker(object):

    def __init__(self):
        named_pipe_logger.info("waiting for fifo at %s" % NAMED_PIPE)
        while not os.path.exists(NAMED_PIPE):
            time.sleep(0.1) # wait for TestListener to create the FIFO
        self.fifo = open(NAMED_PIPE, 'w')

    def __call__(self, msg):
        print >> self.fifo, msg
        self.fifo.flush()
        time.sleep(0.1) # file to settle
 

# Process-blocking helper
# =======================

class Block:
    """Provide routines for blocking on child process actions.

    We require that the caller explicitly pass in the child pid to stop and
    restart, because the caller is the one responsible for terminating the
    child process. If we were to call getpid ourselves, then the proc may have
    already restarted and we'll have the new pid instead of the old: infinite
    loop.

    """

    def __init__(self, pidpath):
        self.pidpath = pidpath

    def getpid(self):
        """Return a pid or None.
        
        You can use stop without implementing this. 

        """
        pid = None
        if os.path.isfile(self.pidpath):
            raw = open(self.pidpath).read()
            if raw:
                pid = int(raw)
        return pid

    def stop(self, pid):
        """Wait for a child process to die.
        """
        try:
            os.waitpid(pid, 0)
        except OSError, err:
            if err.errno != errno.ECHILD: # ECHILD == already reaped 
                raise
        time.sleep(0.2) # log settling
    
    def start(self):
        """Wait for a pid. 
        """
        while self.getpid() is None:
            time.sleep(0.1)
        time.sleep(0.2) # log settling
    
    def restart(self, pid):
        """Given the current child pid, wait for a new one.
        """
        self.stop(pid)
        while self.getpid() == pid:
            time.sleep(0.1)
        time.sleep(0.2) # log settling


def hit_with_timeout(url):
    """This gives the server five seconds to start up and serve our request.
    """
    start = time.time()
    timeout = 5 
    while 1:
        try:
            return urllib.urlopen(url).read()
        except IOError:
            if time.time() - start > timeout:
                raise
            else:
                time.sleep(0.1)

