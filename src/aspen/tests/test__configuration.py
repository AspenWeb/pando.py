import os
import sys
import threading
import urllib

from aspen import server_factory, mode
from aspen._configuration import ConfFile, Configuration as Config
from aspen.tests import assert_raises
from aspen.tests.fsfix import mk, rm


# Fixture
# =======

lib_python = os.path.join('__', 'lib', 'python%s' % sys.version[:3])
sys.path.insert(0, os.path.join('fsfix', lib_python))


# ConfFile
# ========

def test_ConfFile():
    mk(('foo.conf', '[blah]\nfoo = bar\nbaz=True\n[bar]\nbuz=blam\nlaaa=4'))
    conf = ConfFile(os.path.join('fsfix', 'foo.conf'))
    actual = [(k,[t for t in v.iteritems()]) for (k,v) in conf.iteritems()]
    for foo in actual:
        foo[1].sort()
    actual.sort()
    expected = [ ('bar', [ ('buz', 'blam')
                         , ('laaa', '4')])
               , ('blah', [ ('baz', 'True')
                          , ('foo', 'bar')])]
    assert actual == expected, actual


# Configuration
# =============

def test_basic():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\n\naddress = :53700'))
    actual = Config(['-rfsfix']).address
    expected = ('0.0.0.0', 53700)
    assert actual == expected, actual

def test_no_aspen_conf():
    mk()
    actual = Config(['-rfsfix']).address
    expected = ('0.0.0.0', 8080)
    assert actual == expected, actual

def test_no_main_section():
    mk('__/etc', ('__/etc/aspen.conf', '[custom]\nfoo = bar'))
    actual = Config(['-rfsfix']).conf.custom['foo']
    expected = 'bar'
    assert actual == expected, actual

def test_from_aspen_import_config():
    """This actually tests Aspen at a pretty high level.
    """
    mk( '__/etc', lib_python
      , ('__/etc/aspen.conf', '[main]\naddress=:53700\n[my_settings]\nfoo=bar')
      , ('__/etc/apps.conf', '/ foo:wsgi_app')
      , (lib_python+'/foo.py', """\
import aspen

def wsgi_app(environ, start_response):
    my_setting = aspen.conf.my_settings.get('foo', 'default')
    start_response('200 OK', [])
    return ["My setting is %s" % my_setting]
""")
       )
    server = server_factory(Config(['-rfsfix']))
    thread_ = threading.Thread(target=server.start).start()
    expected = "My setting is bar"
    actual = urllib.urlopen('http://localhost:53700/').read()
    server.stop()
    assert actual == expected, actual


# mode
# ====

def test_mode_default():
    mk()
    if 'PYTHONMODE' in os.environ:
        del os.environ['PYTHONMODE']
    Config(['-rfsfix'])
    actual = mode.get()
    expected = 'development'
    assert actual == expected, actual

def test_mode_set_in_conf_file():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nmode=production'))
    if 'PYTHONMODE' in os.environ:
        del os.environ['PYTHONMODE']
    Config(['-rfsfix'])
    actual = mode.get()
    expected = 'production'
    assert actual == expected, actual


# defaults
# ========

def test_default_defaults():
    mk()
    actual = Config(['-rfsfix']).defaults
    expected = ('index.html', 'index.htm')
    assert actual == expected, actual

def test_defaults_space_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo bar'))
    actual = Config(['-rfsfix']).defaults
    expected = ('foo', 'bar')
    assert actual == expected, actual

def test_defaults_comma_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo,bar'))
    actual = Config(['-rfsfix']).defaults
    expected = ('foo', 'bar')
    assert actual == expected, actual

def test_defaults_comma_and_space_separated():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\ndefaults=foo, bar, baz'))
    actual = Config(['-rfsfix']).defaults
    expected = ('foo', 'bar', 'baz')
    assert actual == expected, actual


# threads
# =======

def test_threads_default():
    mk()
    actual = Config(['-rfsfix']).threads
    expected = 10
    assert actual == expected, actual

def test_threads_ten():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=10'))
    actual = Config(['-rfsfix']).threads
    expected = 10
    assert actual == expected, actual

def test_threads_ten_billion():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=10000000000'))
    actual = Config(['-rfsfix']).threads
    expected = 10000000000
    assert actual == expected, actual

def test_threads_zero():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=0000000000'))
    actual = assert_raises(ValueError, Config, ['-rfsfix']).args[0]
    expected = "thread count less than 1: '0'"
    assert actual == expected, actual

def test_threads_negative_one():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=-1'))
    actual = assert_raises(TypeError, Config, ['-rfsfix']).args[0]
    expected = "thread count not a positive integer: '-1'"
    assert actual == expected, actual

def test_threads_blah_blah():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nthreads=blah blah'))
    actual = assert_raises(TypeError, Config, ['-rfsfix']).args[0]
    expected = "thread count not a positive integer: 'blah blah'"
    assert actual == expected, actual


# http_host
# ===========

def test_http_host_default():
    mk()
    actual = Config(['-rfsfix']).http_host
    expected = None
    assert actual is expected, actual

def test_http_host_something():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=foo'))
    actual = Config(['-rfsfix']).http_host
    expected = 'foo'
    assert actual == expected, actual

def test_http_host_empty():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host='))
    actual = assert_raises(ValueError, Config, ['-rfsfix']).args[0]
    expected = "empty http_host"
    assert actual == expected, actual

def test_http_host_includes_protocol():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nhttp_host=http://example.com/'))
    actual = assert_raises(ValueError, Config, ['-rfsfix']).args[0]
    expected = "http_host should not include protocol"
    assert actual == expected, actual


# Test layering: CLI, conf file, environment.
# ===========================================

def test_layering_CLI_trumps_conffile():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\naddress=:9000'))
    actual = Config(['--root', 'fsfix', '--address', ':8080']).address
    expected = ('0.0.0.0', 8080)
    assert actual == expected, actual

def test_layering_CLI_trumps_environment():
    mk()
    actual = Config(['--root', 'fsfix', '--mode', 'production'])._mode
    expected = 'production'
    assert actual == expected, actual

def test_layering_conffile_trumps_environment():
    mk('__/etc', ('__/etc/aspen.conf', '[main]\nmode=production'))
    actual = Config(['--root', 'fsfix'])._mode
    expected = 'production'
    assert actual == expected, actual


# Remove the filesystem fixture after each test, and clear the environment.
# =========================================================================

def teardown():
    rm()
    if 'PYTHONMODE' in os.environ:
        del os.environ['PYTHONMODE']

context = globals()
for name in context.keys():
    if name.startswith('test_'):
        context[name].teardown = teardown
