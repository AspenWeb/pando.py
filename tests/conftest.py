import pytest
from aspen.testing import fsfix
from aspen.testing.fsfix import teardown
from aspen.testing.pytest_fixtures import harness


@pytest.yield_fixture
def mk():
    yield fsfix.mk

def pytest_runtest_teardown():
    teardown()
