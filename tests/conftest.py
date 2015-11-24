from aspen.testing import teardown
from aspen.testing.pytest_fixtures import harness, fs, processor
from aspen.testing.pytest_fixtures import sys_path, sys_path_scrubber


def pytest_runtest_teardown():
    teardown()
