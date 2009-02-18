import os
from subprocess import Popen, PIPE

import aspen
from aspen.tests import LOG, assert_logs, assert_prints
from aspen.tests.fsfix import mk, attach_teardown


LOGGING_TEST_PROGRAM = """\
import logging
import sys

import aspen
aspen.configure(sys.argv[1:])

logging.critical('critical!')
logging.error('error!')
logging.warning('warning!')
logging.info('info!')
logging.debug('debug!')

foo = logging.getLogger('foo')
foo.critical('critical!')
foo.error('error!')
foo.warning('warning!')
foo.info('info!')
foo.debug('debug!')
"""


ARGV = ['python', os.path.join('fsfix', 'aspen-test.py'), '--root=fsfix']


def hit_with_flags(*flags):
    proc = Popen(ARGV + list(flags), stdout=PIPE)
    return proc.communicate()[0]


# Basic
# =====

def test_basic():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('')
    assert_prints( 'critical!'
                 , 'error!'
                 , 'warning!'
                 , 'critical!'
                 , 'error!'
                 , 'warning!'
                 , actual
                  )


# Log Level
# =========

def test_log_level_NIRVANA():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=NIRVANA')
    assert_prints(None, actual)

def test_log_level_CRITICAL():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=CRITICAL')
    assert_prints( 'critical!'
                 , 'critical!'
                 , actual
                  )

def test_log_level_ERROR():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=ERROR')
    assert_prints( 'critical!' , 'error!'
                 , 'critical!' , 'error!'
                 , actual
                  )

def test_log_level_WARNING():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=WARNING')
    assert_prints( 'critical!' , 'error!' , 'warning!'
                 , 'critical!' , 'error!' , 'warning!'
                 , actual
                  )

def test_log_level_INFO():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=INFO')
    assert_prints( 'logging configured from the command line'
                 , 'critical!' , 'error!' , 'warning!' , 'info!'
                 , 'critical!' , 'error!' , 'warning!' , 'info!'
                 , actual
                  )

def test_log_level_DEBUG():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-level=DEBUG')
    assert_prints( 'logging configured from the command line'
                 , 'critical!' , 'error!' , 'warning!' , 'info!' , 'debug!'
                 , 'critical!' , 'error!' , 'warning!' , 'info!' , 'debug!'
                 , 'cleaning up restarter in parent'
                 , actual
                  )


# Filter
# ======

def test_log_filter_basic():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo')
    assert_prints( 'critical!'
                 , 'error!'
                 , 'warning!'
                 , actual
                  )

def test_filtered_log_level_NIRVANA():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=NIRVANA')
    assert_prints(None, actual)

def test_filtered_log_level_CRITICAL():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=CRITICAL')
    assert_prints( 'critical!'
                 , actual
                  )

def test_filtered_log_level_ERROR():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=ERROR')
    assert_prints( 'critical!' , 'error!'
                 , actual
                  )

def test_filtered_log_level_WARNING():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=WARNING')
    assert_prints( 'critical!' , 'error!' , 'warning!'
                 , actual
                  )

def test_filtered_log_level_INFO():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=INFO')
    assert_prints( 'critical!' , 'error!' , 'warning!' , 'info!'
                 , actual
                  )

def test_filtered_log_level_DEBUG():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags('--log-filter=foo', '--log-level=DEBUG')
    assert_prints( 'critical!' , 'error!' , 'warning!' , 'info!' , 'debug!'
                 , actual
                  )


# Format
# ======

def test_formatted():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags( '--log-filter=foo'
                           , '--log-level=ERROR'
                           , '--log-format=foo %(message)s'
                            )
    assert_prints( 'foo critical!' , 'foo error!'
                 , actual
                  )


# File
# ====

def test_log_file():
    mk(('aspen-test.py', LOGGING_TEST_PROGRAM))
    actual = hit_with_flags( '--log-filter=foo'
                           , '--log-level=ERROR'
                           , '--log-file=%s' % LOG
                            )
    assert_logs('critical!' , 'error!', force_unix_EOL=True)


# From aspen.conf
# ===============

def test_aspen_conf_basic():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/aspen.conf', '[logging]\nlevel=INFO') 
       )
    actual = hit_with_flags('')
    assert_prints( 'logging configured from aspen.conf'
                 , 'critical!' , 'error!', 'warning!', 'info!'
                 , 'critical!' , 'error!', 'warning!', 'info!'
                 , actual
                  )

def test_aspen_conf_filter_format():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/aspen.conf', '[logging]\nfilter=foo\nformat=foo %(message)s') 
       )
    actual = hit_with_flags('')
    assert_prints( 'foo critical!' , 'foo error!', 'foo warning!'
                 , actual
                  )

def test_aspen_conf_file():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/aspen.conf', '[logging]\nfile=%s' % LOG) 
       )
    actual = hit_with_flags('')
    assert_logs( 'critical!' , 'error!', 'warning!'
               , 'critical!' , 'error!', 'warning!'
               , force_unix_EOL=True
                )


# From logging.conf
# =================

LOGGING_CONF = """\
[loggers]
keys=root

[handlers]
keys=hand01

[formatters]
keys=form01


[logger_root]
level=INFO
handlers=hand01

[formatter_form01]
format=foo %(message)s

[handler_hand01]
class=StreamHandler
level=INFO
formatter=form01
args=(sys.stdout,)


"""

def test_logging_conf():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/logging.conf', LOGGING_CONF)
       )
    actual = hit_with_flags('')
    assert_prints( 'foo critical!' , 'foo error!', 'foo warning!', 'foo info!'
                 , 'foo critical!' , 'foo error!', 'foo warning!', 'foo info!'
                 , actual
                  )


# Layering
# ========

def test_command_line_trumps_logging_conf():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/logging.conf', LOGGING_CONF)
       )
    actual = hit_with_flags('--log-level=ERROR')
    assert_prints( 'critical!' , 'error!'
                 , 'critical!' , 'error!'
                 , actual
                  )

def test_command_line_trumps_aspen_conf():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/aspen.conf', "[logging]level=CRITICAL")
       )
    actual = hit_with_flags('--log-level=DEBUG', '--log-filter=foo')
    assert_prints( 'critical!' , 'error!', 'warning!', 'info!', 'debug!'
                 , actual
                  )

def test_logging_conf_trumps_aspen_conf():
    mk( ('aspen-test.py', LOGGING_TEST_PROGRAM)
      , ('__/etc/logging.conf', LOGGING_CONF)
      , ('__/etc/aspen.conf', "[logging]level=CRITICAL")
       )
    actual = hit_with_flags('')
    assert_prints( 'foo critical!' , 'foo error!', 'foo warning!', 'foo info!'
                 , 'foo critical!' , 'foo error!', 'foo warning!', 'foo info!'
                 , actual
                  )


attach_teardown(globals())
