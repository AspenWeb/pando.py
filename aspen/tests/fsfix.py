import logging
import os
import re
import sys
from os.path import dirname, isdir, isfile, join, realpath

import aspen
from aspen import simplates
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
    root = realpath('fsfix')
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
    if configure is True:
        aspen.configure(['--root', root])

def expect(path=''):
    """Given a relative path, return an absolute path.

    The incoming path is in UNIX form (/foo/bar.html). The outgoing path is in 
    native form, with symlinks removed.

    """
    path = os.sep.join([dirname(__file__), 'fsfix'] + path.split('/'))
    return realpath(path)

def rm():
    """Remove the filesystem fixture at fsfix/.
    """
    root = realpath('fsfix')
    if isdir(root):
        for root, dirs, files in os.walk(root, topdown=False):
            for name in dirs:
                os.rmdir(join(root, name))
            for name in files:
                os.remove(join(root, name))
        os.rmdir(root)

def teardown():
    """Standard teardown function.
    """
    os.chdir(dirname(__file__))
    rm()
    simplates.__cache = dict() # The simplate cache is process global. Hrm ...
    if '.aspen' in sys.path[0]:
        sys.path = sys.path[1:]
    if 'foo' in sys.modules:
        del sys.modules['foo']
    logging.getLogger().handlers = []

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
    return realpath(join(*parts))
