from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from pytest import raises, mark

from aspen.configuration import Configurable, ConfigurationError, parse
from aspen.configuration.options import OptionParser, DEFAULT
from aspen.website import Website


def test_everything_defaults_to_empty_string():
    o = OptionParser()
    opts, args = o.parse_args([])
    actual = ( opts.configuration_scripts
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
    expected = ( DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT
               , DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT, DEFAULT
                )
    assert actual == expected

def test_logging_threshold_goes_to_one():
    o = OptionParser()
    opts, args = o.parse_args(['-l1'])
    actual = opts.logging_threshold
    expected = '1'
    assert actual == expected

def test_logging_threshold_goes_to_eleven():
    o = OptionParser()
    opts, args = o.parse_args(['--logging_threshold=11'])
    actual = opts.logging_threshold
    expected = '11'
    assert actual == expected


def test_configuration_scripts_can_take_one():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=startup.py'])
    actual = opts.configuration_scripts
    expected = 'startup.py'
    assert actual == expected

def test_configuration_scripts_can_take_two_doesnt_do_anything_special():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=startup.py,uncle.py'])
    actual = opts.configuration_scripts
    expected = 'startup.py,uncle.py'
    assert actual == expected

def test_configuration_scripts_really_doesnt_do_anything_special():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts=Cheese is lovely.'])
    actual = opts.configuration_scripts
    expected = 'Cheese is lovely.'
    assert actual == expected

def test_configuration_scripts_arent_confused_by_io_errors(harness):
    CONFIG = "open('this file should not exist')\n"
    harness.fs.project.mk(('configure-aspen.py', CONFIG),)
    c = Configurable()
    actual = raises(IOError, c.configure, ['-p', harness.fs.project.resolve('.')]).value
    assert actual.strerror == 'No such file or directory'

def test_www_root_defaults_to_cwd():
    c = Configurable()
    c.configure([])
    expected = os.path.realpath(os.getcwd())
    actual = c.www_root
    assert actual == expected

@mark.skipif(sys.platform == 'win32',
             reason="Windows file locking makes this fail")
def test_ConfigurationError_raised_if_no_cwd(harness):
    FSFIX = harness.fs.project.resolve('')
    os.chdir(FSFIX)
    os.rmdir(FSFIX)
    c = Configurable()
    raises(ConfigurationError, c.configure, [])

@mark.skipif(sys.platform == 'win32',
             reason="Windows file locking makes this fail")
def test_ConfigurationError_NOT_raised_if_no_cwd_but_do_have__www_root(harness):
    foo = os.getcwd()
    os.chdir(harness.fs.project.resolve(''))
    os.rmdir(os.getcwd())
    c = Configurable()
    c.configure(['--www_root', foo])
    assert c.www_root == foo

def test_configurable_sees_root_option(harness):
    c = Configurable()
    c.configure(['--www_root', harness.fs.project.resolve('')])
    expected = harness.fs.project.root
    actual = c.www_root
    assert actual == expected

def test_configuration_scripts_works_at_all():
    o = OptionParser()
    opts, args = o.parse_args(['--configuration_scripts', "foo"])
    expected = "foo"
    actual = opts.configuration_scripts
    assert actual == expected

def assert_body(harness, uripath, expected_body):
    actual = harness.simple(filepath=None, uripath=uripath, want='response.body')
    assert actual == expected_body

def test_configuration_script_can_set_renderer_default(harness):
    CONFIG = """
website.renderer_default="stdlib_format"
    """
    SIMPLATE = """
[----]
name="program"
[----] text/html
Greetings, {name}!
    """
    harness.fs.project.mk(('configure-aspen.py', CONFIG),)
    harness.fs.www.mk(('index.spt', SIMPLATE),)
    assert_body(harness, '/', 'Greetings, program!\n')

def test_configuration_script_ignores_blank_indexfilenames():
    w = Website(['--indices', 'index.html,, ,default.html'])
    assert w.indices[0] == 'index.html'
    assert w.indices[1] == 'default.html'
    assert len(w.indices) == 2, "Too many indexfile entries"


# Tests of parsing perversities

def test_parse_charset_good():
    actual = parse.charset(u'UTF-8')
    assert actual == 'UTF-8'

def test_parse_charset_bad():
    raises(ValueError, parse.charset, u'')


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
    raises(TypeError, parse.yes_no, 1)

def test_parse_yes_no_other_is_ValueError():
    raises(ValueError, parse.yes_no, u'cheese')


def test_parse_list_handles_one():
    actual = parse.list_(u'foo')
    assert actual == (False, ['foo'])

def test_parse_list_handles_two():
    actual = parse.list_(u'foo,bar')
    assert actual == (False, ['foo', 'bar'])

def test_parse_list_handles_spaces():
    actual = parse.list_(u' foo ,   bar ')
    assert actual == (False, ['foo', 'bar'])

def test_parse_list_handles_some_spaces():
    actual = parse.list_(u'foo,   bar, baz , buz ')
    assert actual == (False, ['foo', 'bar', 'baz', 'buz'])

def test_parse_list_uniquifies():
    actual = parse.list_(u'foo,foo,bar')
    assert actual == (False, ['foo', 'bar'])

def test_parse_list_extends():
    actual = parse.list_(u'+foo')
    assert actual == (True, ['foo'])


def test_parse_renderer_good():
    actual = parse.renderer(u'stdlib_percent')
    assert actual == u'stdlib_percent'

def test_parse_renderer_bad():
    raises(ValueError, parse.renderer, u'floober')
