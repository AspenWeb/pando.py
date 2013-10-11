import pytest
from aspen.testing import fsfix

@pytest.yield_fixture
def mk():
    yield fsfix.mk
