import os

import aspen


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


def rm():
    """Remove the filesystem fixture at ./fsfix, and run aspen.unconfigure.
    """
    aspen.unconfigure()
    root = os.path.realpath('fsfix')
    if os.path.isdir(root):
        for root, dirs, files in os.walk(root, topdown=False):
            for name in dirs:
                os.rmdir(os.path.join(root, name))
            for name in files:
                os.remove(os.path.join(root, name))
        os.rmdir(root)


def attach_rm(context, prefix):
    """Given a namespace and a routine prefix, attach the rm function.
    """
    for name in context.keys():
        if name.startswith(prefix):
            context[name].teardown = rm


def path(*parts):
    """Given relative path parts, convert to absolute path on the filesystem.
    """
    return os.path.realpath(os.path.join(*parts))
