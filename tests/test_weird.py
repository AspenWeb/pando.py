"""Wherein our hero learns about sys.path_importer_cache.

Python caches some of its import machinery, and if you try really hard, you can
shoot yourself in the foot with that.

"""
import os
import sys
from pprint import pformat


FIX_VIA_IMPORT = 1
FIX_VIA_PROJ = 0
FSFIX = os.path.realpath('fsfix')


def log(a, *b):
    return  # turn off logging now that this works
    if not b:
        print a.rjust(30)
    else:
        for line in b:
            print a.rjust(30)+": ", line


def rm():
    root = FSFIX
    if os.path.isdir(root):
        for root, dirs, files in os.walk(root, topdown=False):
            for name in dirs:
                _ = os.path.join(root, name)
                log("removing  dir", _)
                os.rmdir(_)
            for name in files:
                _ = os.path.join(root, name)
                log("removing file", _)
                os.remove(_)
        log("removing root", root)
        os.rmdir(root)
    sys.path_importer_cache = {}

def __dump():
    log("sys.path_importer_cache", pformat(sys.path_importer_cache).splitlines())

def test_weirdness():
    try:
        #print
        foo = os.path.join(FSFIX, 'foo')
        foo = os.path.realpath(foo)
        if foo not in sys.path:
            log("inserting into sys.path", foo )
            sys.path.insert(0, foo)

        log("making directory", FSFIX)
        os.mkdir(FSFIX)
        if FIX_VIA_PROJ:
            log("making directory", FSFIX + '/foo')
            os.mkdir(FSFIX + '/foo')

        log("importing a thing")
        old = set(sys.path_importer_cache.keys())
        import aspen
        now = set(sys.path_importer_cache.keys())
        log("diff", now - old)

        rm()

        log("making directory", FSFIX)
        os.mkdir(FSFIX)
        log("making directory", FSFIX + '/foo')
        os.mkdir(FSFIX + '/foo')
        log("making file", FSFIX + '/foo' + '/bar.py')
        open(FSFIX + '/foo/bar.py', 'w+').write('baz = "buz"')

        log("contents of fsfix/foo/bar.py", open('fsfix/foo/bar.py').read())
        log("contents of sys.path", *sys.path)

        log("importing bar")
        __dump()
        try:
            import bar
            log("succeeded")
        except:
            log("failed")
            raise
    finally:
        rm()

    #print

if __name__ == '__main__':
    test_weirdness()
