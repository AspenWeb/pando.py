"""
:mod:`harness`
--------------
"""

import os
import sys
from collections import namedtuple

from filesystem_tree import FilesystemTree

from .client import Client


CWD = os.getcwd()


def teardown():
    """Standard teardown function.

    - reset the current working directory
    - remove FSFIX = %{tempdir}/fsfix
    - clear out sys.path_importer_cache

    """
    os.chdir(CWD)
    # Reset some process-global caches. Hrm ...
    sys.path_importer_cache = {}  # see test_weird.py in aspen


teardown()  # start clean


class Harness:
    """A harness to be used in the Pando test suite itself. Probably not useful to you.
    """

    def __init__(self):
        self.fs = namedtuple('fs', 'www project')
        self.fs.www = FilesystemTree()
        self.fs.project = FilesystemTree()
        self.client = Client(self.fs.www.root, self.fs.project.root)

    def teardown(self):
        self.fs.www.remove()
        self.fs.project.remove()

    # Simple API
    # ==========

    def simple(
        self, contents='Greetings, program!', filepath='index.html.spt', uripath=None,
        website_configuration=None, **kw
    ):
        """A helper to create a file and hit it through our machinery.
        """
        if filepath is not None:
            self.fs.www.mk((filepath, contents))
        if website_configuration is not None:
            self.client.hydrate_website(**website_configuration)

        if uripath is None:
            if filepath is None:
                uripath = '/'
            else:
                uripath = '/' + filepath
                if uripath.endswith('.spt'):
                    uripath = uripath[:-len('.spt')]
                for indexname in self.client.website.request_processor.indices:
                    if uripath.endswith(indexname):
                        uripath = uripath[:-len(indexname)]
                        break

        return self.client.GET(uripath, **kw)

    def make_request(self, *a, **kw):
        kw['return_after'] = 'dispatch_path_to_filesystem'
        kw['want'] = 'request'
        return self.simple(*a, **kw)

    def make_dispatch_result(self, *a, **kw):
        kw['return_after'] = 'dispatch_path_to_filesystem'
        kw['want'] = 'dispatch_result'
        return self.simple(*a, **kw)
