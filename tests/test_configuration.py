from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from pytest import raises, mark

from aspen.request_processor import ConfigurationError, RequestProcessor, parse


def test_defaults_to_defaults(harness):
    rp = RequestProcessor()
    actual = ( rp.project_root
             , rp.www_root

             , rp.changes_reload
             , rp.charset_dynamic
             , rp.charset_static
             , rp.indices
             , rp.media_type_default
             , rp.media_type_json
             , rp.renderer_default
              )
    expected = ( None, os.getcwd(), False, 'UTF-8', None
               , ['index.html', 'index.json', 'index', 'index.html.spt', 'index.json.spt', 'index.spt']
               , 'text/plain', 'application/json', 'stdlib_percent'
                )
    assert actual == expected

def test_www_root_defaults_to_cwd():
    p = RequestProcessor()
    expected = os.path.realpath(os.getcwd())
    actual = p.www_root
    assert actual == expected

@mark.skipif(sys.platform == 'win32',
             reason="Windows file locking makes this fail")
def test_ConfigurationError_raised_if_no_cwd(harness):
    FSFIX = harness.fs.project.resolve('')
    os.chdir(FSFIX)
    os.rmdir(FSFIX)
    raises(ConfigurationError, RequestProcessor)

@mark.skipif(sys.platform == 'win32',
             reason="Windows file locking makes this fail")
def test_ConfigurationError_NOT_raised_if_no_cwd_but_do_have__www_root(harness):
    foo = os.getcwd()
    os.chdir(harness.fs.project.resolve(''))
    os.rmdir(os.getcwd())
    rp = RequestProcessor(www_root=foo)
    assert rp.www_root == foo

def test_processor_sees_root_option(harness):
    rp = RequestProcessor(www_root=harness.fs.project.resolve(''))
    expected = harness.fs.project.root
    actual = rp.www_root
    assert actual == expected

def test_user_can_set_renderer_default(harness):
    SIMPLATE = """
[----]
name="program"
[----]
Greetings, {name}!
    """
    harness.request_processor.renderer_default="stdlib_format"
    harness.fs.www.mk(('index.html.spt', SIMPLATE),)
    actual = harness.simple(filepath=None, uripath='/', want='output.body')
    assert actual == 'Greetings, program!\n'

def test_configuration_ignores_blank_indexfilenames():
    rp = RequestProcessor(indices='index.html,, ,default.html')
    assert rp.indices[0] == 'index.html'
    assert rp.indices[1] == 'default.html'
    assert len(rp.indices) == 2, "Too many indexfile entries"


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
    raises(AttributeError, parse.yes_no, 1)

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
