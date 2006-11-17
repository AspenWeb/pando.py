#!/usr/bin/env python
from distutils.core import setup

from aspen import __version__

classifiers = [
    'Development Status :: 3 - Alpha'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: Freeware'
  , 'Natural Language :: English'
  , 'Operating System :: MacOS :: MacOS X'
  , 'Operating System :: Microsoft :: Windows'
  , 'Operating System :: POSIX'
  , 'Programming Language :: Python'
  , 'Topic :: Internet :: WWW/HTTP :: HTTP Servers'
                ]

setup( name = 'aspen'
     , version = __version__
     , package_dir = {'':'site-packages'}
     , packages = ['aspen']
     , scripts = ['bin/aspen']
     , description = 'aspen is a robust and sane Python webserver.'
     , author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , url = 'http://www.zetadev.com/software/aspen/'
     , classifiers = classifiers
      )
