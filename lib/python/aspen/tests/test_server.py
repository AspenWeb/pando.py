import time
import threading
import urllib
from pprint import pformat
from subprocess import Popen, PIPE

import aspen
from aspen import restarter
from aspen.server import Server
from aspen.tests.fsfix import mk, attach_teardown
from aspen.tests import assert_logs, log, set_log_filter, set_log_format


# Fixture
# =======

def check(url, response, log_filter=''):
    configuration = aspen.configure(['--root=fsfix'])
    server = Server(configuration)
    t = threading.Thread(target=server.start)
    t.start()
    time.sleep(0.2) # give server time to start up; since BaseServer.start does 
                    # so much, we can't really set a flag when start-up is 
                    # deterministically accomplished
    try:
        expected = response
        actual = urllib.urlopen(url).read()
        assert actual == expected, actual
    finally:
        server.stop()
        t.join()


# Tests
# =====

def test_basic():
    mk(('index.html', 'foo'))
    check("http://localhost:8080/", "foo")

def test_log():
    mk(('index.html', 'bar'))
    set_log_filter('aspen')
    check("http://localhost:8080/", "bar")
    assert_logs( "logging is already configured"
               , "No apps configured."
               , "No handlers configured; using defaults."
               , "No middleware configured."
               , "starting on ('0.0.0.0', 8080)"
               , "configuring filesystem monitor"
               , "No app found for '/'"
               , "cleaning up server"
               , force_unix_EOL=True
                )

def test_from_aspen_import_config():
    """multi-test for app, conf, address
    """
    mk( '__/etc'
      , '__/lib/python' 
      , ('__/etc/aspen.conf', '[main]\naddress=:53700\n[my_settings]\nfoo=bar')
      , ('__/etc/apps.conf', '/ foo:wsgi_app')
      , ('__/lib/python/foo.py', """\
import aspen

def wsgi_app(environ, start_response):
    my_setting = aspen.conf.my_settings.get('foo', 'default')
    start_response('200 OK', [])
    return ["My setting is %s" % my_setting]
""")
       )
    check("http://localhost:53700/", "My setting is bar")


def test_thread_clobbering():
    """nasty test to ensure restarter thread gets stopped

    This is actually a restarter problem, but this is the test that found it so
    I'm leaving it in here.

    """
    def test(run_num):
        set_log_format("%(threadName)s  %(message)s")
        def log_threads(i):
            log.debug("%s%s: %s" % (i, run_num, pformat(threading.enumerate()[1:])))
            time.sleep(1)
        mk()
        configuration = aspen.configure(['--root=fsfix'])
        server = Server(configuration)
        t = threading.Thread(target=server.start)
        t.setDaemon(True)
        t.start()
        log_threads(' 1')
#        time.sleep(0.2) # give server.start time to run; log_threads sleeps
        server.stop()
        log_threads(' 2')
        t.join()
        log_threads(' 3')
    yield test, 'a'
    log.debug("")
    yield test, 'b'


attach_teardown(globals())
