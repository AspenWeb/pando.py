from os.path import dirname, join

try:
    import setuptools  # noqa
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import find_packages, setup

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
     , description = ('Pando is a Python web framework. '
                      'Simplates are the main attraction.')
     , long_description=open(join(dirname(__file__), 'README.rst')).read()
     , entry_points = {'console_scripts': ['fcgi_pando = fcgi_pando:main [fcgi]']}
     , name = 'pando'
     , packages = find_packages(exclude=['pando.tests', 'pando.tests.*'])
     , py_modules = ['fcgi_pando']
     , url = 'http://aspen.io/'
     , version = version
     , zip_safe = False
     , package_data = {'pando': ['www/*', 'configuration/mime.types']}
     , install_requires = open('requirements.txt').read()
     , extras_require = {'fcgi': ['flup']}
     , tests_require = open('requirements_tests.txt').read()
      )
