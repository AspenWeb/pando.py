import pytest
from aspen.testing import fsfix
from aspen.testing.filesystem_fixture import FilesystemFixture
from aspen.testing.fsfix import teardown
from aspen.testing.harness import Harness
from aspen.website import Website


@pytest.yield_fixture
def mk():
    yield fsfix.mk

@pytest.yield_fixture
def harness():
    www = FilesystemFixture()
    project = FilesystemFixture()
    website = Website(['--www_root', www.root, '--project_root', project.root])
    yield Harness(website, www, project)

def pytest_runtest_teardown():
    teardown()
