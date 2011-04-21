import sys

from aspen.configuration import Configuration


def test_nirvana():
    actual = c = Configuration(['-vNIRVANA']).opts.log_level
    expected = sys.maxint
    assert actual == expected, actual
