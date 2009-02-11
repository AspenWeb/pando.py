import os

import aspen
from aspen.tests.fsfix import mk, attach_teardown


def test_absolutize_root_short():
    mk()
    argv = ['-rfsfix']
    expected = ['-r%s' % os.path.realpath('fsfix')]
    actual = aspen.absolutize_root(argv)
    assert actual == expected, actual

def test_absolutize_root_short_space():
    mk()
    argv = ['-r', 'fsfix']
    expected = ['-r', os.path.realpath('fsfix')]
    actual = aspen.absolutize_root(argv)
    assert actual == expected, actual

def test_absolutize_root_long(): # this tests a bunch of other conditions
    mk()
    argv = [ '--address=:5000'
           , '--root=fsfix'
           , '--mode=flimmer' # no validation here
           , 'blahblahblah ahbl' # like, seriously
           , '--log-level=DEBUG'
           #, '--log-filter=foo' # only flags given are passed through
           , '--log-format=bar'
           , '--log-file=log'
            ]
    expected = argv[:]
    expected[1] = '--root=%s' % os.path.realpath('fsfix')  # absolutized 
    actual = aspen.absolutize_root(argv) # list order preserved
    assert actual == expected, actual

def test_absolutize_root_long_space():
    mk()
    argv = ['--root', 'fsfix']
    expected = ['--root', os.path.realpath('fsfix')]
    actual = aspen.absolutize_root(argv)
    assert actual == expected, actual


attach_teardown(globals())
