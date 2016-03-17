try:
    import setuptools  # noqa
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import find_packages, setup

from build import ASPEN_DEPS, TEST_DEPS

version = open('version.txt').read()


classifiers = [ 'Development Status :: 4 - Beta'
              , 'Environment :: Console'
              , 'Intended Audience :: Developers'
              , 'License :: OSI Approved :: MIT License'
              , 'Natural Language :: English'
              , 'Operating System :: OS Independent'
              , 'Programming Language :: Python :: 2.7'
              , 'Programming Language :: Python :: Implementation :: CPython'
              , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
               ]

setup( author = 'Chad Whitacre et al.'
     , author_email = 'team@aspen.io'
     , classifiers = classifiers
     , description = ('Aspen is a Python web framework. '
                      'Simplates are the main attraction.')
     , entry_points = {'console_scripts': ['fcgi_aspen = fcgi_aspen:main [fcgi]']}
     , name = 'aspen'
     , packages = find_packages(exclude=['aspen.tests', 'aspen.tests.*'])
     , py_modules = ['fcgi_aspen']
     , url = 'http://aspen.io/'
     , version = version
     , zip_safe = False
     , package_data = {'aspen': ['www/*', 'configuration/mime.types']}
     , install_requires = ASPEN_DEPS
     , extras_require = {'fcgi': ['flup']}
     , tests_require = TEST_DEPS
      )
