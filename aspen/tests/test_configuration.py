import os
import logging
import sys

from aspen.configuration import Configurable, ConfigurationError
from aspen.configuration.optparser import validate_address, callback_root
from aspen.tests import assert_raises
from aspen.tests.fsfix import attach_teardown, expect, mk


def test_nirvana():
    logging.getLogger().handlers = []  # override nose logging nosiness
    c = Configurable()
    c.configure(['-vNIRVANA'])
    actual = c.log_level
    expected = sys.maxint
    assert actual == expected, actual

def test_callback_root_fails_when_directory_doesnt_exist():
    assert_raises(ConfigurationError, callback_root, None, None, 'fsfix', None)

def test_root_defaults_to_cwd():
    mk()
    c = Configurable()
    c.configure([])
    expected = os.getcwd()
    actual = c.root
    assert actual == expected, actual

def test_configurable_sees_root_option():
    mk()
    c = Configurable()
    c.configure(['--root', 'fsfix'])
    expected = os.getcwd()
    actual = c.root
    assert actual == expected, actual

def test_callback_root_finds_root():
    mk()
    expected = expect()
    class Values():
        pass
    class Parser:
        values = Values()
    parser = Parser()
    callback_root(None, None, 'fsfix', parser)
    expected = os.path.realpath("fsfix")
    actual = parser.values.root

    assert actual == expected, actual

def test_address_can_be_localhost():
    expected = (('127.0.0.1', 8000), 2)
    actual = validate_address('localhost:8000')
    print actual
    assert actual == expected, actual


attach_teardown(globals())
