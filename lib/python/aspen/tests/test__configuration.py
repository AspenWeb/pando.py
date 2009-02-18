import re
import os
import sys
import threading
import urllib

from aspen import mode, configure, unconfigure
from aspen._configuration import ConfFile, Configuration as Config
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, attach_teardown


# ConfFile
# ========

def test_ConfFile():
    mk(('foo.conf', '[blah]\nfoo = bar\nbaz=True\n[bar]\nbuz=blam\nlaaa=4'))
    conf = ConfFile(os.path.join('fsfix', 'foo.conf'))
    expected = [ ('bar', [ ('buz', 'blam')
                         , ('laaa', '4')])
               , ('blah', [ ('baz', 'True')
                          , ('foo', 'bar')])]
    actual = [(k,[t for t in v.iteritems()]) for (k,v) in conf.iteritems()]
    for foo in actual:
        foo[1].sort()
    actual.sort()
    assert actual == expected, actual


# Configuration
# =============

def test_basic():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\n\naddress = :53700'))
    expected = ('0.0.0.0', 53700)
    actual = Config(['--root=fsfix']).address
    assert actual == expected, actual

def test_no_aspen_conf():
    mk()
    expected = ('0.0.0.0', 8080)
    actual = Config(['--root=fsfix']).address
    assert actual == expected, actual

def test_no_main_section():
    mk('__/etc', ('__/etc/aspen.conf', '[custom]\nfoo = bar'))
    expected = 'bar'
    actual = Config(['--root=fsfix']).conf.custom['foo']
    assert actual == expected, actual


# mode
# ====

def test_mode_default():
    mk()
    if 'PYTHONMODE' in os.environ:
        del os.environ['PYTHONMODE']
    Config(['--root=fsfix'])
    expected = 'development'
    actual = mode.get()
    assert actual == expected, actual

def test_mode_set_in_conf_file():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nmode=production'))
    if 'PYTHONMODE' in os.environ:
        del os.environ['PYTHONMODE']
    Config(['--root=fsfix'])
    expected = 'production'
    actual = mode.get()
    assert actual == expected, actual


# defaults
# ========

def test_default_defaults():
    mk()
    expected = ('index.html', 'index.htm')
    actual = Config(['--root=fsfix']).defaults
    assert actual == expected, actual

def test_defaults_space_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo bar'))
    expected = ('foo', 'bar')
    actual = Config(['--root=fsfix']).defaults
    assert actual == expected, actual

def test_defaults_comma_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo,bar'))
    expected = ('foo', 'bar')
    actual = Config(['--root=fsfix']).defaults
    assert actual == expected, actual

def test_defaults_comma_and_space_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo, bar, baz'))
    expected = ('foo', 'bar', 'baz')
    actual = Config(['--root=fsfix']).defaults
    assert actual == expected, actual


# threads
# =======

def test_threads_default():
    mk()
    expected = 10
    actual = Config(['--root=fsfix']).threads
    assert actual == expected, actual

def test_threads_ten():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=10'))
    expected = 10
    actual = Config(['--root=fsfix']).threads
    assert actual == expected, actual

def test_threads_ten_billion():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=10000000000'))
    expected = 10000000000
    actual = Config(['--root=fsfix']).threads
    assert actual == expected, actual

def test_threads_zero():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=0000000000'))
    expected = "thread count less than 1: '0'"
    actual = assert_raises(ValueError, Config, ['--root=fsfix']).args[0]
    assert actual == expected, actual

def test_threads_negative_one():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=-1'))
    expected = "thread count not a positive integer: '-1'"
    actual = assert_raises(TypeError, Config, ['--root=fsfix']).args[0]
    assert actual == expected, actual

def test_threads_blah_blah():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=blah blah'))
    expected = "thread count not a positive integer: 'blah blah'"
    actual = assert_raises(TypeError, Config, ['--root=fsfix']).args[0]
    assert actual == expected, actual


# http_version
# ============

def test_http_version_default():
    mk()
    actual = Config(['--root=fsfix']).http_version
    expected = '1.1'
    assert actual == expected, actual

def test_http_version_explicit_default():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_version=1.1'))
    actual = Config(['--root=fsfix']).http_version
    expected = '1.1'
    assert actual == expected, actual

def test_http_version_1_0():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_version=1.0'))
    actual = Config(['--root=fsfix']).http_version
    expected = '1.0'
    assert actual == expected, actual

def test_http_version_0_9():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_version=0.9'))
    actual = assert_raises(TypeError, Config, ['--root=fsfix']).args[0]
    expected = "http_version must be 1.0 or 1.1, not '0.9'"
    assert actual == expected, actual

def test_http_version_anything_else():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_version=HTTP/1.2'))
    actual = assert_raises(TypeError, Config, ['--root=fsfix']).args[0]
    expected = "http_version must be 1.0 or 1.1, not 'HTTP/1.2'"
    assert actual == expected, actual


# pidfile 
# =======

def test_pidfile____var():
    mk('__/var')
    configuration = Config(['--root', 'fsfix'])
    actual = configuration.pidfile.path
    expected = os.path.realpath(os.path.join('fsfix', '__', 'var', 'aspen.pid'))
    assert actual == expected, actual


# daemon
# ======

def test_daemon_only_when_wanted():
    mk()
    configuration = Config(['--root', 'fsfix'])
    expected = None
    actual = configuration.daemon
    assert actual is expected, actual


# Test layering: CLI, conf file, environment.
# ===========================================

def test_layering_CLI_trumps_conffile():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\naddress=:9000'))
    expected = ('0.0.0.0', 8080)
    actual = Config(['--root', 'fsfix', '--address', ':8080']).address
    assert actual == expected, actual

def test_layering_CLI_trumps_environment():
    mk()
    expected = 'production'
    actual = Config(['--root', 'fsfix', '--mode', 'production'])._mode
    assert actual == expected, actual

def test_layering_conffile_trumps_environment():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nmode=production'))
    expected = 'production'
    actual = Config(['--root', 'fsfix'])._mode
    assert actual == expected, actual


attach_teardown(globals())
