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
    'Cheroot>=4.0.0beta',
    'mimeparse>=0.1.3',
    'first>=2.0.1',
    'algorithm>=1.0.0',
    'filesystem_tree>=1.0.0',
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
    './vendor/virtualenv-1.11.2.py',
    '--prompt=[aspen]',
    '--extra-search-dir=' + BOOTSTRAP_DIR,
    ]


def _virt(cmd, envdir='env'):
    return os.path.join(envdir, 'bin', cmd)


def _virt_version():
    _env()
    v = shell(_virt('python'), '-c',
              'import sys; print(sys.version_info[:2])')
    return eval(v)


def _env():
    if os.path.exists('env'):
        return
    args = [main.options.python] + ENV_ARGS + ['env']
    run(*args)


def aspen():
    if os.path.exists(_virt('aspen')):
        return
    _env()
    for dep in ASPEN_DEPS:
        run(_virt('pip'), 'install', '--no-index',
            '--find-links=' + INSTALL_DIR, dep)
    run(_virt('python'), 'setup.py', 'develop')


def dev():
    _env()
    # pytest will need argparse if its running under 2.6
    if _virt_version() < (2, 7):
        TEST_DEPS.insert(0, 'argparse')
    for dep in TEST_DEPS:
        run(_virt('pip'), 'install', '--no-index',
            '--find-links=' + TEST_DIR, dep)
    run(_virt('pip'), 'install', 'sphinx')


def clean_env():
    shell('rm', '-rf', 'env')


def clean():
    autoclean()
    shell('find', '.', '-name', '*.pyc', '-delete')
    clean_env()
    clean_smoke()
    clean_jenv()
    clean_test()
    clean_build()
    clean_sphinx()


# Doc / Smoke
# ===========

smoke_dir = 'smoke-test'


def docs():
    aspen()
    run(_virt('pip'), 'install', 'aspen-tornado')
    run(_virt('pip'), 'install', 'pygments')
    shell(_virt('aspen'), '-a:5370', '-wdoc', '-pdoc/.aspen',
          '--changes_reload=1', silent=False)


def sphinx():
    dev()
    sphinxopts = []
    builddir = 'sphinx-build'
    run('mkdir', '-p', builddir)
    newenv = os.environ
    newenv.update({'PYTHONPATH': 'env/lib/python2.7/site-packages'})
    args = ['-b', 'html', '-d', builddir + '/doctrees', sphinxopts, 'sphinx-src', builddir + '/html' ]
    run(_virt('sphinx-build'), args, env=newenv)


def clean_sphinx():
    shell('rm', '-rf', 'sphinx-build')


def smoke():
    aspen()
    run('mkdir', smoke_dir)
    open(os.path.join(smoke_dir, "index.html"), "w").write("Greetings, program!")
    run(_virt('aspen'), '-w', smoke_dir)


def clean_smoke():
    shell('rm', '-rf', smoke_dir)


# Testing
# =======

def test():
    aspen()
    dev()
    shell(_virt('py.test'), 'tests/', ignore_status=True, silent=False)


def pylint():
    _env()
    run(_virt('pip'), 'install', 'pylint')
    run(_virt('pylint'), '--rcfile=.pylintrc',
        'aspen', '|', 'tee', 'pylint.out', shell=True, ignore_status=True)


def analyse():
    pylint()
    dev()
    aspen()
    run(_virt('py.test'),
        '--junitxml=testresults.xml',
        '--cov-report', 'term',
        '--cov-report', 'xml',
        '--cov', 'aspen',
        'tests/',
        ignore_status=False)
    print('done!')


def clean_test():
    clean_env()
    shell('rm', '-f', '.coverage', 'coverage.xml', 'testresults.xml', 'pylint.out')

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
    for dep in ASPEN_DEPS + TEST_DEPS:
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
    docs - run the doc server
    smoke - run a smoke test
    test - run the unit tests
    analyse - run the unit tests with code coverage enabled
    pylint - run pylint on the source
    clean - remove all build artifacts
    clean_{env,jenv,smoke,test,jtest} - clean some build artifacts

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
