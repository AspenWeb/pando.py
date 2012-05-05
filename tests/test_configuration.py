import os
import socket

import aspen
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

             , opts.changes_reload
             , opts.charset_dynamic
             , opts.charset_static
             , opts.indices
             , opts.media_type_default
             , opts.media_type_json
             , opts.renderer_default
             , opts.show_tracebacks
              )
    expected = ( DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT
               , DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT
                )
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
    actual = parse.network_address(u'localhost:8000')
    assert actual == expected, actual

def test_configuration_scripts_works_at_all():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts', "foo"])
    expected = "foo"
    actual = opts.configuration_scripts
    assert actual == expected, actual



def test_parse_charset_good():
    actual = parse.charset(u'UTF-8')
    assert actual == 'UTF-8', actual

def test_parse_charset_bad():
    assert_raises(ValueError, parse.charset, u'')


def test_parse_yes_no_yes_is_True():
    assert parse.yes_no(u'yEs')

def test_parse_yes_no_true_is_True():
    assert parse.yes_no(u'trUe')

def test_parse_yes_no_1_is_True():
    assert parse.yes_no(u'1')

def test_parse_yes_no_no_is_False():
    assert not parse.yes_no(u'nO')

def test_parse_yes_no_true_is_False():
    assert not parse.yes_no(u'FalSe')

def test_parse_yes_no_1_is_False():
    assert not parse.yes_no(u'0')

def test_parse_yes_no_int_is_AttributeError():
    assert_raises(TypeError, parse.yes_no, 1)

def test_parse_yes_no_other_is_ValueError():
    assert_raises(ValueError, parse.yes_no, u'cheese')


def test_parse_list_handles_one():
    actual = parse.list_(u'foo')
    assert actual == (False, ['foo']), actual

def test_parse_list_handles_two():
    actual = parse.list_(u'foo,bar')
    assert actual == (False, ['foo', 'bar']), actual

def test_parse_list_handles_spaces():
    actual = parse.list_(u' foo ,   bar ')
    assert actual == (False, ['foo', 'bar']), actual

def test_parse_list_handles_some_spaces():
    actual = parse.list_(u'foo,   bar, baz , buz ')
    assert actual == (False, ['foo', 'bar', 'baz', 'buz']), actual

def test_parse_list_uniquifies():
    actual = parse.list_(u'foo,foo,bar')
    assert actual == (False, ['foo', 'bar']), actual

def test_parse_list_extends():
    actual = parse.list_(u'+foo')
    assert actual == (True, ['foo']), actual


def test_parse_renderer_good():
    actual = parse.renderer(u'pystache')
    assert actual == u'pystache', actual

def test_parse_renderer_bad():
    assert_raises(ValueError, parse.renderer, u'floober')


def test_parse_network_engine_good():
    actual = parse.network_engine(u'cherrypy')
    assert actual == 'cherrypy', actual

def test_parse_network_engine_bad():
    assert_raises(ValueError, parse.network_engine, u'floober')


def test_parse_network_address_unix_socket():
    actual = parse.network_address(u"/foo/bar")
    assert actual == ("/foo/bar", socket.AF_UNIX), actual

def test_parse_network_address_unix_socket_fails_on_windows():
    oldval = aspen.WINDOWS
    try:
        aspen.WINDOWS = True
        assert_raises(ValueError, parse.network_address, u"/foo/bar")
    finally:
        aspen.WINDOWS = oldval

def test_parse_network_address_notices_ipv6():
    actual = parse.network_address(u"2607:f0d0:1002:51::4")
    assert actual == (u"2607:f0d0:1002:51::4", socket.AF_INET6), actual

def test_parse_network_address_sees_one_colon_as_ipv4():
    actual = parse.network_address(u"192.168.1.1:8080")
    assert actual == ((u"192.168.1.1", 8080), socket.AF_INET), actual

def test_parse_network_address_need_colon_for_ipv4():
    assert_raises(ValueError, parse.network_address, u"192.168.1.1 8080")

def test_parse_network_address_defaults_to_inaddr_any():
    actual = parse.network_address(u':8080')
    assert actual == ((u'0.0.0.0', 8080), socket.AF_INET), actual

def test_parse_network_address_with_bad_address():
    assert_raises(ValueError, parse.network_address, u'0 0 0 0:8080')

def test_parse_network_address_with_bad_port():
    assert_raises(ValueError, parse.network_address, u':80 0')

def test_parse_network_address_with_port_too_low():
    actual = assert_raises(ValueError, parse.network_address, u':-1').args[0]
    assert actual == "invalid port (out of range)", actual

def test_parse_network_address_with_port_too_high():
    actual = assert_raises(ValueError, parse.network_address, u':65536').args[0]
    assert actual == "invalid port (out of range)", actual

attach_teardown(globals())
