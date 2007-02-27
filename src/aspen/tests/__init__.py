def assert_raises(Exc, call, *arg, **kw):
    """Given an Exception, a callable, and its params, return an exception.
    """
    exc = None
    try:
        call(*arg, **kw)
    except Exception, exc:
        pass
    assert exc is not None, "no exception; expected %s" % Exc
    assert isinstance(exc, Exc), "raised %s, not %s" % (str(exc), str(Exc))
    return exc


BIN_ASPEN = '''\
#!/usr/bin/env python
"""Simulate the bin/aspen script, with package location.

This script (and by extension, the tests that call it) can be run anywhere next
to or below the aspen package.

"""
import os
import sys

def find_aspen(path):
    if 'aspen' in os.listdir(path):
        return path
    elif path != os.sep:
        return find_aspen(os.path.dirname(path))
    else:
        raise EnvironmentError("could not find the aspen package")

sys.path.insert(0, find_aspen(os.getcwd()))

import aspen
aspen.main()
'''
