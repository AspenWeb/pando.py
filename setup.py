from os.path import dirname, join

from setuptools import find_packages, setup


setup(
    author='Chad Whitacre et al.',
    author_email='team@aspen.io',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    description='Pando is a Python web framework. Simplates are the main attraction.',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    long_description_content_type='text/x-rst',
    name='pando',
    packages=find_packages(exclude=['pando.tests', 'pando.tests.*']),
    url='http://aspen.io/',
    version=open('version.txt').read().strip(),
    zip_safe=False,
    package_data={'pando': ['www/*', 'configuration/mime.types']},
    install_requires=open('requirements.txt').read(),
    tests_require=open('requirements_tests.txt').read(),
)
