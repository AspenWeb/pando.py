#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import xmlrpclib

HERE = os.path.dirname(os.path.abspath(__file__))
DEPS_FILE = os.path.join(HERE, 'deps.txt')
PYPI_ENDPOINT = 'http://pypi.python.org/pypi'


def main():
    retcode = 0
    client = xmlrpclib.ServerProxy(PYPI_ENDPOINT)
    for name, version in sorted(get_current_versions(DEPS_FILE).items()):
        if not report_version_status(
                name, version, max(client.package_releases(name))):
            retcode = 1
    return retcode


def get_current_versions(deps_file):
    with open(deps_file) as df:
        return dict((
            l.strip().split() for l in df.readlines()
            if l.strip()
        ))


def report_version_status(name, version, latest_available):
    if latest_available > version:
        retcode = 1
        print((
            '{} {} is available!  ' +
            'Current dependency is version {}.  Upgrade!').format(
                name, latest_available, version
            )
        )
        return False
    print('{} {} is the latest available!'.format(name, version))
    return True


if __name__ == '__main__':
    sys.exit(main())
