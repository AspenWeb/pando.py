from ez_setup import use_setuptools
use_setuptools()

from setuptools import find_packages, setup


classifiers = [
    'Development Status :: 4 - Beta'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: OSI Approved :: MIT License'
  , 'Natural Language :: English'
  , 'Operating System :: MacOS :: MacOS X'
  , 'Operating System :: Microsoft :: Windows'
  , 'Operating System :: POSIX'
  , 'Programming Language :: Python'
  , 'Topic :: Internet :: WWW/HTTP :: HTTP Servers'
   ]

setup( author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , classifiers = classifiers
     , description = ('Aspen is an async web app server. '
                      'Simplates are the thing about it.')
     , entry_points = { 'console_scripts': ['aspen = aspen.cli:main'] }
     , name = 'aspen'
     , packages = find_packages() 
     , url = 'http://aspen.io/'
     , version = '~~VERSION~~'
     , install_requires = ['diesel == 1.9.7b'] # waiting for public release
     , zip_safe = False
      )
