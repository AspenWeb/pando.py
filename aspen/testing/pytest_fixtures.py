import sys

import pytest
from aspen.testing.filesystem_fixture import FilesystemFixture
from aspen.testing.harness import Harness


@pytest.yield_fixture
def fs():
    fs = FilesystemFixture()
    yield fs
    fs.remove()


@pytest.yield_fixture
def module_scrubber():
    before = set(sys.modules.keys())
    yield
    after = set(sys.modules.keys())
    for name in after - before:
        del sys.modules[name]


@pytest.yield_fixture
def sys_path_scrubber():
    before = set(sys.path)
    yield
    after = set(sys.path)
    for name in after - before:
        sys.path.remove(name)


@pytest.yield_fixture
def sys_path(fs, module_scrubber):
    sys.path.insert(0, fs.root)
    yield fs


@pytest.yield_fixture
def harness(module_scrubber, sys_path_scrubber):
    harness = Harness()
    yield harness
    harness.teardown()
