from __future__ import division, print_function, unicode_literals, with_statement

import os
import sys
import os.path
from fabricate import ExecutionError, main, run, shell, autoclean

# Core Executables
# ================

PANDO_DEPS = [
    'python-mimeparse>=0.1.4',
    'first>=2.0.1',
    'algorithm>=1.1.0',
    'filesystem_tree>=1.0.1',
    'dependency_injection>=1.1.0',
    ('aspen', 'https://github.com/AspenWeb/aspen.py/archive/master.zip'),
    ]

TEST_DEPS = [
    'coverage>=3.7.1',
    'cov-core>=1.7',
    'py>=1.4.20',
    'pytest>=2.5.2',
    'pytest-cov>=1.6',
    ]

ENV_ARGS = [
    '-m', 'virtualenv',
    '--prompt=[pando]',
    ]


def _virt(cmd, envdir='env'):
    envdir = _env(envdir)
    if os.name == "nt":
        return os.path.join(envdir, 'Scripts', cmd + '.exe')
    else:
        return os.path.join(envdir, 'bin', cmd)


def _virt_version(envdir):
    v = shell(_virt('python', envdir), '-c',
              'import sys; print(sys.version_info[:2])')
    return eval(v)


def _env(envdir='env'):

    # http://stackoverflow.com/a/1883251
    if hasattr(sys, 'real_prefix'):
        # We're already inside someone else's virtualenv.
        return sys.prefix
    elif hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        # We're already inside someone else's pyvenv.
        return sys.prefix
    elif os.path.exists(envdir):
        # We've already built our own virtualenv.
        return envdir

    args = [sys.executable] + ENV_ARGS + [envdir]
    run(*args)
    return envdir


def env():
    """set up a base virtual environment"""
    _env()


def _deps(envdir):
    run(_virt('pip', envdir), 'install', *[d[1] if isinstance(d, tuple) else d for d in PANDO_DEPS])


def _test_deps(envdir):
    run(_virt('pip', envdir), 'install', *TEST_DEPS)


def _dev(envdir='env'):
    envdir = _env(envdir)
    _deps(envdir)
    _test_deps(envdir)
    try:
        shell(_virt('pip', envdir), 'show', 'pando')
    except ExecutionError:
        run(_virt('pip', envdir), 'install', '--no-deps', '--editable', '.')
    return envdir


def dev():
    """set up an environment able to run pando and the tests"""
    _dev()


def clean_env():
    """clean env artifacts"""
    shell('rm', '-rf', 'env')


def clean():
    """clean all artifacts"""
    autoclean()
    shell('find', '.', '-name', '*.pyc', '-delete')
    clean_env()
    clean_sphinx()
    clean_jenv()
    clean_test()
    clean_build()


# Docs
# ====


def docserve():
    """run the aspen website"""
    envdir = _deps()
    run(_virt('pip', envdir), 'install', 'aspen-tornado')
    run(_virt('pip', envdir), 'install', 'pygments')
    shell(_virt('python', envdir), '-m', 'aspen_io', silent=False)


def _sphinx_cmd(packages, cmd):
    envdir = _deps(envdir='denv')
    for p in packages:
        run(_virt('pip', envdir='denv'), 'install', p)
    sphinxopts = []
    builddir = 'docs/_build'
    run('mkdir', '-p', builddir)
    newenv = os.environ
    newenv.update({'PYTHONPATH': 'denv/lib/python2.7/site-packages'})
    args = ['-b', 'html', '-d', builddir + '/doctrees', sphinxopts,
            'docs', builddir + '/html']
    run(_virt(cmd, envdir=envdir), args, env=newenv)

def sphinx():
    """build sphinx documents"""
    _sphinx_cmd(['sphinx'], "sphinx-build")

def autosphinx():
    """run sphinx-autobuild"""
    _sphinx_cmd(['sphinx', 'sphinx-autobuild'], "sphinx-autobuild")

def clean_sphinx():
    """clean sphinx artifacts"""
    shell('rm', '-rf', 'docs/_build')
    shell('rm', '-rf', 'denv')


# Testing
# =======

def test():
    """run all tests"""
    shell(_virt('py.test', _dev()), 'tests/', ignore_status=True, silent=False)


def testf():
    """run tests, stopping at the first failure"""
    shell(_virt('py.test', _dev()), '-x', 'tests/', ignore_status=True, silent=False)


def pylint():
    """run lint"""
    envdir = _env()
    run(_virt('pip', envdir), 'install', 'pylint')
    run(_virt('pylint', envdir), '--rcfile=.pylintrc',
        'pando', '|', 'tee', 'pylint.out', shell=True, ignore_status=True)


def test_cov():
    """run code coverage"""
    run(_virt('py.test', _dev()),
        '--junitxml=testresults.xml',
        '--cov-report', 'term',
        '--cov-report', 'xml',
        '--cov-report', 'html',
        '--cov', 'pando',
        'tests/',
        ignore_status=False)


def analyse():
    """run lint and coverage"""
    pylint()
    test_cov()
    print('done!')


def clean_test():
    """clean test artifacts"""
    clean_env()
    shell('rm', '-rf', '.coverage', 'coverage.xml', 'testresults.xml', 'htmlcov', 'pylint.out')

# Build
# =====


def build():
    """build an egg"""
    run(sys.executable, 'setup.py', 'bdist_egg')


def wheel():
    """build a wheel"""
    run(sys.executable, 'setup.py', 'bdist_wheel')


def clean_build():
    """clean build artifacts"""
    run('python', 'setup.py', 'clean', '-a')
    run('rm', '-rf', 'dist')

# Jython
# ======
JYTHON_URL = "http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7-b1/jython-installer-2.7-b1.jar"

def _jython_home():
    if not os.path.exists('jython_home'):
        local_jython = 'jython-installer.jar'
        run('wget', JYTHON_URL, '-qO', local_jython)
        run('java', '-jar', local_jython, '-s', '-d', 'jython_home')

def _jenv():
    _jython_home()
    jenv = dict(os.environ)
    jenv['PATH'] = os.path.join('.', 'jython_home', 'bin') + ':' + jenv['PATH']
    args = [ 'jython' ] + ENV_ARGS + [ '--python=jython', 'jenv' ]
    run(*args, env=jenv)

def clean_jenv():
    """clean up the jython environment"""
    shell('find', '.', '-name', '*.class', '-delete')
    shell('rm', '-rf', 'jenv', 'jython_home')

def jython_test():
    """install jython and run tests with coverage (requires java)"""
    _jenv()
    run(_virt('pip', 'jenv'), 'install', *TEST_DEPS)
    run(_virt('jython', 'jenv'), 'setup.py', 'develop')
    run(_virt('jython', 'jenv'), _virt('py.test', 'jenv'),
            '--junitxml=jython-testresults.xml', 'tests',
            '--cov-report', 'term',
            '--cov-report', 'xml',
            '--cov', 'pando',
            ignore_status=True)

def clean_jtest():
    """clean jython test results"""
    shell('find', '.', '-name', '*.class', '-delete')
    shell('rm', '-rf', 'jython-testresults.xml')


def show_targets():
    """show the list of valid targets (this list)"""
    print("Valid targets:\n")
    # organize these however
    targets = ['show_targets', None,
               'env', 'dev', 'testf', 'test', 'pylint', 'test_cov', 'analyse', None,
               'build', 'wheel', None,
               'docserve', 'sphinx', 'autosphinx', None,
               'clean', 'clean_env', 'clean_test', 'clean_build', 'clean_sphinx', None,
               'jython_test', None,
               'clean_jenv', 'clean_jtest', None,
               ]
    #docs = '\n'.join(["  %s - %s" % (t, LOCALS[t].__doc__) for t in targets])
    #print(docs)

    for t in targets:
        if t is not None:
            print("  %s - %s" % (t, LOCALS[t].__doc__))
        else:
            print("")

    if len(targets) < (len(LOCALS) - len(NON_TARGETS)):
        missed = set(LOCALS.keys()).difference(NON_TARGETS, targets)
        print("Unordered targets: " + ', '.join(sorted(missed)))
    sys.exit()


LOCALS = dict(locals())
NON_TARGETS = [ 'main', 'autoclean', 'run', 'shell' ]
NON_TARGETS += list(x for x in LOCALS if x.startswith('_') or not callable(LOCALS[x] ))

if __name__ == '__main__':
    main( default='show_targets'
        , ignoreprefix="python"  # workaround for gh190
         )
