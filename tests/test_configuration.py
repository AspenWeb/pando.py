import os

from aspen.configuration import Configurable, ConfigurationError, parse
from aspen.configuration.options import OptionParser, DEFAULT
from aspen.testing import assert_raises
from aspen.testing.fsfix import attach_teardown, FSFIX, mk


def test_everything_defaults_to_empty_string():
    o = OptionParser()
    opts, args = o.parse_args([])
    actual = ( opts.configuration_scripts
             , opts.network_address
             , opts.network_engine
             , opts.logging_threshold
             , opts.project_root
             , opts.www_root

             , opts.changes_kill
             , opts.charset_dynamic
             , opts.charset_static
             , opts.indices
             , opts.media_type_default
             , opts.media_type_json
             , opts.show_tracebacks
              )
    expected = (DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT)
    expected += (DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT)
    assert actual == expected, actual

def test_logging_threshold_goes_to_one():
    o = OptionParser()
    opts, args = o.parse_args(['-l1'])
    actual = opts.logging_threshold
    expected = '1'
    assert actual == expected, actual

def test_logging_threshold_goes_to_eleven():
    o = OptionParser()
    opts, args = o.parse_args(['--logging_threshold=11'])
    actual = opts.logging_threshold
    expected = '11'
    assert actual == expected, actual


def test_configuration_scripts_can_take_one():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=startup.py'])
    actual = opts.configuration_scripts
    expected = 'startup.py'
    assert actual == expected, actual

def test_configuration_scripts_can_take_two_doesnt_do_anything_special():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=startup.py,uncle.py'])
    actual = opts.configuration_scripts
    expected = 'startup.py,uncle.py'
    assert actual == expected, actual

def test_configuration_scripts_really_doesnt_do_anything_special():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=Cheese is lovely.'])
    actual = opts.configuration_scripts
    expected = 'Cheese is lovely.'
    assert actual == expected, actual


def test_www_root_defaults_to_cwd():
    mk()
    c = Configurable()
    c.configure([])
    expected = os.path.realpath(os.getcwd())
    actual = c.www_root
    assert actual == expected, actual

def test_ConfigurationError_raised_if_no_cwd():
    mk()
    os.chdir(FSFIX)
    os.rmdir(FSFIX)
    c = Configurable()
    assert_raises(ConfigurationError, c.configure, [])

def test_ConfigurationError_NOT_raised_if_no_cwd_but_do_have__www_root():
    mk()
    foo = os.getcwd()
    os.chdir(FSFIX)
    os.rmdir(os.getcwd())
    c = Configurable()
    c.configure(['--www_root', foo])
    expected = foo
    actual = c.www_root
    assert actual == expected, actual

def test_configurable_sees_root_option():
    mk()
    c = Configurable()
    c.configure(['--www_root', FSFIX])
    expected = os.getcwd()
    actual = c.www_root
    assert actual == expected, actual

def test_address_can_be_localhost():
    expected = (('127.0.0.1', 8000), 2)
    actual = parse.network_address('localhost:8000')
    assert actual == expected, actual

def test_configuration_scripts_works_at_all():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts', "foo"])
    expected = "foo"
    actual = opts.configuration_scripts
    assert actual == expected, actual


attach_teardown(globals())
