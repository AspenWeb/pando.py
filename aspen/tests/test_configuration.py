import logging
import sys

from aspen.configuration import Configurable, ConfigurationError, find_root
from aspen.configuration.optparser import validate_address
from aspen.tests import assert_raises
from aspen.tests.fsfix import attach_teardown, expect, mk


def test_nirvana():
    logging.getLogger().handlers = []  # override nose logging nosiness
    c = Configurable()
    c.configure(['-vNIRVANA'])
    actual = c.log_level
    expected = sys.maxint
    assert actual == expected, actual


def test_find_root_fails_when_directory_doesnt_exist():
    assert_raises(ConfigurationError, find_root, ['fsfix'])


def test_find_root_finds_root():
    mk()
    expected = expect()
    actual = find_root(['fsfix'])
    assert actual == expected, actual


def test_address_can_be_localhost():
    expected = (('127.0.0.1', 8000), 2)
    actual = validate_address('localhost:8000')
    print actual
    assert actual == expected, actual


attach_teardown(globals())
