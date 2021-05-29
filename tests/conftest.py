from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

import pytest
from pando.testing.harness import Harness, teardown
from filesystem_tree import FilesystemTree


@pytest.fixture
def fs():
    fs = FilesystemTree()
    yield fs
    fs.remove()


@pytest.fixture
def sys_path_scrubber():
    before = set(sys.path)
    yield
    after = set(sys.path)
    for name in after - before:
        sys.path.remove(name)


@pytest.fixture
def sys_path(fs):
    sys.path.insert(0, fs.root)
    yield fs


@pytest.fixture
def harness(sys_path_scrubber):
    harness = Harness()
    yield harness
    harness.teardown()


@pytest.fixture
def client(harness):
    yield harness.client


@pytest.fixture
def website(client):
    yield client.website


def pytest_runtest_teardown():
    teardown()
