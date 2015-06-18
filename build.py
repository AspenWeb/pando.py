from __future__ import division, print_function, unicode_literals, with_statement

import os
import sys
import os.path
from optparse import make_option
from fabricate import main, run, shell, autoclean

# Core Executables
# ================
# We satisfy dependencies using local tarballs, to ensure that we can build
# without a network connection. They're kept in our repo in ./vendor.

ASPEN_DEPS = [
    'mimeparse>=0.1.3',
    'first>=2.0.1',
    'algorithm>=1.0.0',
    'filesystem_tree>=1.0.1',
    'dependency_injection>=1.1.0',
    ]

TEST_DEPS = [
    'coverage>=3.7.1',
    'cov-core>=1.7',
    'py>=1.4.20',
    'pytest>=2.5.2',
    'pytest-cov>=1.6',
    ]

INSTALL_DIR = './vendor/install'
TEST_DIR = './vendor/test'
BOOTSTRAP_DIR = './vendor/bootstrap'

ENV_ARGS = [
    './vendor/virtualenv-13.0.3.py',
    '--prompt=[aspen]',
    '--extra-search-dir=' + BOOTSTRAP_DIR,
    ]


def _virt(cmd, envdir='env'):
    envdir = _env(envdir)
    if os.name == "nt":
        return os.path.join(envdir, 'Scripts', cmd + '.exe')
    else:
        return os.path.join(envdir, 'bin', cmd)


def _virt_version():
    _env()
    v = shell(_virt('python'), '-c',
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

    args = [main.options.python] + ENV_ARGS + [envdir]
    run(*args)
    return envdir


def env():
    _env()


def deps(envdir='env'):
    envdir = _env(envdir)
    v = shell(_virt('python', envdir), '-c', 'import aspen; print("found")', ignore_status=True)
    if b"found" in v:
        return
    for dep in ASPEN_DEPS:
        run(_virt('pip', envdir), 'install', '--no-index',
            '--find-links=' + INSTALL_DIR, dep)
    run(_virt('python', envdir), 'setup.py', 'develop')


def dev_deps(envdir='env'):
    envdir = deps(envdir)
    # pytest will need argparse if it's running under 2.6
    if _virt_version() < (2, 7):
        TEST_DEPS.insert(0, 'argparse')
    for dep in TEST_DEPS:
        run(_virt('pip', envdir), 'install', '--no-index',
            '--find-links=' + TEST_DIR, dep)


def clean_env():
    shell('rm', '-rf', 'env')


def clean():
    autoclean()
    shell('find', '.', '-name', '*.pyc', '-delete')
    clean_env()
    clean_smoke()
    clean_sphinx()
    clean_jenv()
    clean_test()
    clean_build()


# Doc / Smoke
# ===========

smoke_dir = 'smoke-test'


def docserve():
    deps()
    run(_virt('pip'), 'install', 'aspen-tornado')
    run(_virt('pip'), 'install', 'pygments')
    shell(_virt('python'), '-m', 'aspen', '-wdoc', '-pdoc/.aspen', silent=False)


def smoke():
    deps()
    run('mkdir', smoke_dir)
    open(os.path.join(smoke_dir, "index.html"), "w").write("Greetings, program!")
    run(_virt('python'), '-m', 'aspen', '-w', smoke_dir)


def clean_smoke():
    shell('rm', '-rf', smoke_dir)


def _sphinx_cmd(packages, cmd):
    envdir = deps(envdir='denv')
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
    _sphinx_cmd(['sphinx'], "sphinx-build")

def autosphinx():
    _sphinx_cmd(['sphinx', 'sphinx-autobuild'], "sphinx-autobuild")

def clean_sphinx():
    shell('rm', '-rf', 'docs/_build')
    shell('rm', '-rf', 'denv')


# Testing
# =======

def test():
    dev_deps()
    shell(_virt('py.test'), 'tests/', ignore_status=True, silent=False)


def testf():
    dev_deps()
    shell(_virt('py.test'), '-x', 'tests/', ignore_status=True, silent=False)


def pylint():
    env()
    run(_virt('pip'), 'install', 'pylint')
    run(_virt('pylint'), '--rcfile=.pylintrc',
        'aspen', '|', 'tee', 'pylint.out', shell=True, ignore_status=True)


def test_cov():
    dev_deps()
    run(_virt('py.test'),
        '--junitxml=testresults.xml',
        '--cov-report', 'term',
        '--cov-report', 'xml',
        '--cov-report', 'html',
        '--cov', 'aspen',
        'tests/',
        ignore_status=False)


def analyse():
    dev_deps()
    pylint()
    test_cov()
    print('done!')


def clean_test():
    clean_env()
    shell('rm', '-rf', '.coverage', 'coverage.xml', 'testresults.xml', 'htmlcov', 'pylint.out')

# Build
# =====


def build():
    run(main.options.python, 'setup.py', 'bdist_egg')


def wheel():
    run(main.options.python, 'setup.py', 'bdist_wheel')


def clean_build():
    run('python', 'setup.py', 'clean', '-a')
    run('rm', '-rf', 'dist')

# Jython
# ======
JYTHON_URL = "http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7-b1/jython-installer-2.7-b1.jar"

def _jython_home():
    if not os.path.exists('jython_home'):
        local_jython = os.path.join('vendor', 'jython-installer.jar')
        run('wget', JYTHON_URL, '-qO', local_jython)
        run('java', '-jar', local_jython, '-s', '-d', 'jython_home')

def _jenv():
    _jython_home()
    jenv = dict(os.environ)
    jenv['PATH'] = os.path.join('.', 'jython_home', 'bin') + ':' + jenv['PATH']
    args = [ 'jython' ] + ENV_ARGS + [ '--python=jython', 'jenv' ]
    run(*args, env=jenv)

def clean_jenv():
    shell('find', '.', '-name', '*.class', '-delete')
    shell('rm', '-rf', 'jenv', 'vendor/jython-installer.jar', 'jython_home')

def jython_test():
    _jenv()
    for dep in TEST_DEPS:
        run(_virt('pip', 'jenv'), 'install', os.path.join('vendor', dep))
    run(_virt('jython', 'jenv'), 'setup.py', 'develop')
    run(_virt('jython', 'jenv'), _virt('py.test', 'jenv'),
            '--junitxml=jython-testresults.xml', 'tests',
            '--cov-report', 'term',
            '--cov-report', 'xml',
            '--cov', 'aspen',
            ignore_status=True)

def clean_jtest():
    shell('find', '.', '-name', '*.class', '-delete')
    shell('rm', '-rf', 'jython-testresults.xml')

def show_targets():
    print("""Valid targets:

    show_targets (default) - this
    build - build an aspen egg
    aspen - set up a test aspen environment in env/
    dev - set up an environment able to run tests in env/
    docserve - run the doc server
    sphinx - build the html docs in docs/_build/html
    autosphinx - run sphinx-autobuild on the module to auto-pickup changes
    smoke - run a smoke test
    test - run the unit tests
    analyse - run the unit tests with code coverage enabled
    pylint - run pylint on the source
    clean - remove all build artifacts
    clean_{env,jenv,sphinx,smoke,test,jtest} - clean some build artifacts

    jython_test - install jython and run unit tests with code coverage.
                  (requires java)
    """)
    sys.exit()

extra_options = [
        make_option('--python', action="store", dest="python", default="python"),
        ]

main( extra_options=extra_options
    , default='show_targets'
    , ignoreprefix="python"  # workaround for gh190
     )
