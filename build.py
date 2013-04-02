import sys
import os.path
from optparse import make_option
from fabricate import main, run, autoclean

# Core Executables
# ================
# We satisfy dependencies using local tarballs, to ensure that we can build 
# without a network connection. They're kept in our repo in ./vendor.

ASPEN_DEPS = [ 'Cheroot-4.0.0beta.tar.gz', 'mimeparse-0.1.3.tar.gz', 'tornado-1.2.1.tar.gz' ]

TEST_DEPS = [ 'coverage-3.5.3.tar.gz', 'nose-1.1.2.tar.gz', 'nosexcover-1.0.7.tar.gz', 'snot-0.6.tar.gz' ]

def _virt(cmd, envdir='env'):
    return os.path.join(envdir, 'bin', cmd)

ENV_ARGS = [  
            './vendor/virtualenv-1.7.1.2.py', 
            '--distribute',
            '--unzip-setuptools',
            '--prompt="[aspen] "',
            '--never-download',
            '--extra-search-dir=./vendor/',
            ]

def _env():
    args = [ main.options.python ] + ENV_ARGS + [ 'env' ]
    run(*args)

def aspen():
    _env()
    for dep in ASPEN_DEPS:
        run(_virt('pip'), 'install', os.path.join('vendor', dep))
    run(_virt('python'), 'setup.py', 'develop')

def dev():
    _env()
    for dep in TEST_DEPS:
        run(_virt('pip'), 'install', os.path.join('vendor', dep))

def clean():
    autoclean()


# Doc / Smoke
# ===========

def docs():
    aspen()
    run(_virt('aspen'), '-a:5370', '-wdoc', '-pdoc/.aspen', '--changes_reload=1')

def smoke():
    aspen()
    testdir = 'smoke-test'
    run('mkdir', testdir)
    open(os.path.join(testdir, "index.html"),"w").write("Greetings, program!")
    run(_virt('aspen'), '-w', testdir)

# Testing
# =======

def test():
    aspen()
    dev()
    run(_virt('nosetests'), '-sx', 'tests/')

def pylint():
    _env()
    run(_virt('pip'), 'install', 'pylint')
    run(_virt('pylint'), '--rcfile=.pylintrc', 'aspen')

def analyse():
    pylint()
    dev()
    run(_virt('nosetests'), 
            '--with-xcoverage', 
            '--with-xunit', 'tests', 
            '--cover-package', 'aspen')
    print('done!')

# Build
# =====

def build():
    run(main.options.python, 'setup.py', 'bdist_egg')

# Jython
# ======
JYTHON_URL="http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.5.3/jython-installer-2.5.3.jar" 

def _jython_home():
    local_jython = os.path.join('vendor', 'jython-installer.jar')
    run('wget', JYTHON_URL, '-O', local_jython)
    run('java', '-jar', local_jython, '-s', '-d', 'jython_home')

def _jenv():
    _jython_home()
    jpath = os.path.join('.', 'jython_home', 'bin') + ':' + os.environ['PATH']
    args = ['PATH=' + jpath, 'jython' ] + ENV_ARGS + [ '--python=jython', 'jenv' ] 
    run(*args)
    # always required for jython since it's ~= python 2.5
    run(_virt('pip', 'jenv'), 'install', 'simplejson')


def jython_test():
    _jenv()
    for dep in ASPEN_DEPS + TEST_DEPS:
        run(_virt('pip', 'jenv'), 'install', os.path.join('vendor', dep))
    run(_virt('jython', 'jenv'), 'setup.py', 'develop')
    run(_virt('jython', 'jenv'), _virt('nosetests', 'jenv'), '--with-xunit', 'tests',
        '--xunit-file=jython-nosetests.xml',
	'--cover-package', 'aspen'
	)

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
    
    jython_test - install jython and run unit tests with code coverage. 
                  (requires java)
    """)
    sys.exit()

extra_options = [ 
        make_option('--python', action="store", dest="python", default="python"),
        ]

main(extra_options=extra_options, default='show_targets')
