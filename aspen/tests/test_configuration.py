import logging
import sys

from aspen.configuration import Configurable
from aspen.tests.fsfix import attach_teardown


def test_nirvana():
    logging.getLogger().handlers = [] # override nose logging nosiness
    c = Configurable()
    c.configure(['-vNIRVANA'])
    actual = c.log_level
    expected = sys.maxint
    assert actual == expected, actual


attach_teardown(globals())
