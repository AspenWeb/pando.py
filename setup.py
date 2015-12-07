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
              , 'Programming Language :: Python :: 2.6'
              , 'Programming Language :: Python :: 2.7'
              , 'Programming Language :: Python :: Implementation :: CPython'
              , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
               ]


tests_require = open('tests/requirements.txt').read().splitlines()

setup( author = 'Gratipay, LLC'
     , author_email = 'support@gratipay.com'
     , classifiers = classifiers
     , description = ('Aspen is a Python web framework. '
                      'Simplates are the main attraction.')
     , name = 'aspen'
     , packages = find_packages(exclude=['aspen.tests', 'aspen.tests.*'])
     , url = 'http://aspen.io/'
     , version = version
     , zip_safe = False
     , package_data = {'aspen': ['configuration/mime.types']}
     , install_requires = [ 'python-mimeparse==0.1.4'
                          , 'first==2.0.1'
                          , 'algorithm>=1.0.0'
                          , 'filesystem_tree>=1.0.0'
                           ]
     , tests_require = tests_require
      )
