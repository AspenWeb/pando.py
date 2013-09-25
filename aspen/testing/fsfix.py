import os
import sys
import shutil
import tempfile
import traceback
from os.path import dirname, isdir, join, realpath
from aspen import resources, sockets

CWD = os.getcwd()
FSFIX = os.path.realpath(os.path.join(tempfile.gettempdir(), 'fsfix'))


def convert_path(path):
    """Given a Unix path, convert it for the current platform.
    """
    return os.sep.join(path.split('/'))

def convert_paths(paths):
    """Given a tuple of Unix paths, convert them for the current platform.
    """
    return tuple([convert_path(p) for p in paths])

def mk(*treedef):
    """Given a treedef, build a filesystem fixture in FSFIX.

    treedef is a sequence of strings and tuples. If a string, it is interpreted
    as a path to a directory that should be created. If a tuple, the first
    element is a path to a file, the second is the contents of the file. We do
    it this way to ease cross-platform testing.

    """
    root = FSFIX
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
            parent = dirname(path)
            if not isdir(parent):
                os.makedirs(parent)
            file(path, 'w').write(contents)

def fix(path=''):
    """Given a relative path, return an absolute path under FSFIX.

    The incoming path is in UNIX form (/foo/bar.html). The outgoing path is in
    native form, with symlinks removed.

    """
    path = os.sep.join([FSFIX] + path.split('/'))
    return realpath(path)

def rm():
    """Remove the filesystem fixture at FSFIX.
    """
    if isdir(FSFIX):
        shutil.rmtree(FSFIX)

def teardown_function(function):
    teardown()

def teardown():
    """Standard teardown function.

    - reset the current working directory
    - remove FSFIX = %{tempdir}/fsfix
    - reset Aspen's global state
    - remove '.aspen' from sys.path
    - remove 'foo' from sys.modules
    - clear out sys.path_importer_cache
    - clear out execution.extras

    """
    os.chdir(CWD)
    rm()
    # Reset some process-global caches. Hrm ...
    resources.__cache__ = {}
    sockets.__sockets__ = {}
    sockets.__channels__ = {}
    sys.path_importer_cache = {} # see test_weird.py
    if 'fsfix' in sys.path[0]:
        sys.path = sys.path[1:]
    if 'foo' in sys.modules:
        del sys.modules['foo']
    import aspen.execution
    aspen.execution.clear_changes()

teardown() # start clean

def torndown(func):
    func.teardown = teardown
    return func

def path(*parts):
    """Given relative path parts, convert to absolute path on the filesystem.
    """
    return realpath(join(*parts))
