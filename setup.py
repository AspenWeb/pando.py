from distribute_setup import use_setuptools
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
              , 'Programming Language :: Python :: 2.5'
              , 'Programming Language :: Python :: 2.6'
              , 'Programming Language :: Python :: 2.7'
              , 'Programming Language :: Python :: Implementation :: CPython'
              , 'Programming Language :: Python :: Implementation :: Jython'
              , 'Topic :: Internet :: WWW/HTTP :: HTTP Servers'
               ]

setup( author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , classifiers = classifiers
     , description = ('Aspen is a Python web framework. '
                      'Simplates are the main attraction.')
     , entry_points = { 'console_scripts': [ 'aspen = aspen.server:main'
                                           , 'thrash = thrash:main'
                                           , 'swaddle = swaddle:main'
                                            ] }
     , name = 'aspen'
     , packages = find_packages(exclude=[ 'aspen.tests'
                                        , 'aspen.tests.*'
                                         ])
     , py_modules = ['swaddle', 'thrash']
     , url = 'http://aspen.io/'
     , version = version
     , zip_safe = False
     , package_data = {'aspen': [ 'www/*'
                                , 'configuration/mime.types'
                                 ]}
      )
