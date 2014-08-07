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
              , 'Operating System :: MacOS :: MacOS X'
              , 'Operating System :: Microsoft :: Windows'
              , 'Operating System :: POSIX'
              , 'Programming Language :: Python :: 2.6'
              , 'Programming Language :: Python :: 2.7'
              , 'Programming Language :: Python :: Implementation :: CPython'
              , 'Programming Language :: Python :: Implementation :: Jython'
              , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
               ]

setup( author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
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
     , install_requires = [ 'mimeparse==0.1.3'
                          , 'first==2.0.1'
                          , 'algorithm>=1.0.0'
                          , 'filesystem_tree>=1.0.0'
                           ]
     , extras_require = {'fcgi': ['flup']}
     , tests_require = [ 'virtualenv>=1.11'
                       , 'py'
                       , 'coverage'
                       , 'pytest'
                       , 'pytest-cov'
                        ]
      )
