"""
aspen.testing.pytest_fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

import pytest
from aspen.testing.harness import Harness
from filesystem_tree import FilesystemTree


@pytest.yield_fixture
def fs():
    fs = FilesystemTree()
    yield fs
    fs.remove()


@pytest.yield_fixture
def sys_path_scrubber():
    before = set(sys.path)
    yield
    after = set(sys.path)
    for name in after - before:
        sys.path.remove(name)


@pytest.yield_fixture
def sys_path(fs):
    sys.path.insert(0, fs.root)
    yield fs


@pytest.yield_fixture
def harness(sys_path_scrubber):
    harness = Harness()
    yield harness
    harness.teardown()


@pytest.yield_fixture
def client(harness):
    yield harness.client
