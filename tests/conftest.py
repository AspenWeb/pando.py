import pytest
from aspen.testing import fsfix
from aspen.testing.fsfix import teardown


@pytest.yield_fixture
def mk():
    yield fsfix.mk

def pytest_runtest_teardown():
    teardown()

