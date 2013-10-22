import pytest
from aspen.testing import fsfix
from aspen.testing.fsfix import teardown
from aspen.testing.pytest_fixtures import fs, harness, sys_path, module_scrubber


@pytest.yield_fixture
def mk():
    yield fsfix.mk

def pytest_runtest_teardown():
    teardown()
