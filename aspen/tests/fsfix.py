import commands
import os
import re
import signal

import aspen
from aspen import restarter
from aspen.tests import reset_log_filter, reset_log_format
from nose.tools import with_setup


def convert_path(path):
    """Given a Unix path, convert it for the current platform.
    """
    return os.sep.join(path.split('/'))


def convert_paths(paths):
    """Given a tuple of Unix paths, convert them for the current platform.
    """
    return tuple([convert_path(p) for p in paths])


def mk(*treedef, **kw):
    """Given a treedef, build a filesystem fixture in ./fsfix.

    treedef is a sequence of strings and tuples. If a string, it is interpreted
    as a path to a directory that should be created. If a tuple, the first
    element is a path to a file, the second is the contents of the file. We do
    it this way to ease cross-platform testing.

    The one meaningful keyword argument is configure. If True, mk will call
    aspen.configure with ./fsfix as the root.

    """
    configure = kw.get('configure', False)
    root = os.path.realpath('fsfix')
    os.mkdir(root)
    for item in treedef:
        if isinstance(item, basestring):
            path = convert_path(item.lstrip('/'))
            path = os.sep.join([root, path])
            os.makedirs(path)
        elif isinstance(item, tuple):
            filepath, contents = item
            path = convert_path(filepath.lstrip('/'))
            path = os.sep.join([root, path])
            parent = os.path.dirname(path)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            file(path, 'w').write(contents)
    if configure is True:
        aspen.configure(['--root', root])


pid_re = re.compile('^\s*(\d*) .*$')
def kill_aspen_test():
    """Kill any lingering test processes (this doesn't work on, um, Windows).

    I thought of extending this to also kill aspen processes (for 
    test_tutorial) but then what happens if you run this on a production box? 
    So kill those yourself.

    We sort the pids for test_ipc_daemon. I think what happens is if you kill
    the child first and reap it ourselves, then the parent never completes? Or 
    something? Can't get to the bottom of it now. :^(

    """
    cmd = "ps xww | grep 'fsfix/aspen-test' | grep -v 'grep'" # portable?!
    raw = commands.getoutput(cmd).splitlines()
    pids = []
    for line in raw:
        match = pid_re.match(line)
        if match is not None:
            pid = int(match.group(1))
            pids.append(pid)
    pids.sort() # kill parent before child, but why?
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            os.wait()
        except OSError:
            pass # if parent is terminated first, killing child lands here


def rm():
    """Remove the filesystem fixture at fsfix/.
    """
    root = os.path.realpath('fsfix')
    if os.path.isdir(root):
        for root, dirs, files in os.walk(root, topdown=False):
            for name in dirs:
                os.rmdir(os.path.join(root, name))
            for name in files:
                os.remove(os.path.join(root, name))
        os.rmdir(root)


def teardown():
    """Standard teardown function.
    """
    rm()
    reset_log_filter()
    reset_log_format()
    #if restarter.MONITORING:
    #    restarter.stop_monitoring()
    #else:
    #    restarter._initialize() # recreate _monitor thread in case it was used
    open('log', 'r+').truncate(0)

teardown() # start clean


def attach_teardown(context, prefix='test_'):
    """Given a namespace and a routine prefix, attach the teardown function.
    """
    for name, func in context.items():
        if name.startswith(prefix):
            func = with_setup(teardown=teardown)(func) # non-destructive

def torndown(func):
    func.teardown = teardown
    return func


def path(*parts):
    """Given relative path parts, convert to absolute path on the filesystem.
    """
    return os.path.realpath(os.path.join(*parts))
