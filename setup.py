from distutils.core import setup


classifiers = [
    'Development Status :: 3 - Alpha'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: OSI Approved :: BSD License'
  , 'Natural Language :: English'
  , 'Operating System :: MacOS :: MacOS X'
  , 'Operating System :: Microsoft :: Windows'
  , 'Operating System :: POSIX'
  , 'Programming Language :: Python'
  , 'Topic :: Internet :: WWW/HTTP :: HTTP Servers'
  , 'Topic :: Internet :: WWW/HTTP :: WSGI'
  , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
  , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Server'
   ]

setup( name = 'aspen'
     , version = '0.3'
     , package_dir = {'':'src'}
     , packages = ['aspen']
     , scripts = ['bin/aspen']
     , description = 'Aspen is a highly extensible Python webserver.'
     , author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , url = 'http://www.zetadev.com/software/aspen/'
     , classifiers = classifiers
      )
