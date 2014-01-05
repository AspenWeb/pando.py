from aspen.testing.harness import teardown
from aspen.testing.pytest_fixtures import client, harness, fs
from aspen.testing.pytest_fixtures import sys_path, sys_path_scrubber


def pytest_runtest_teardown():
    teardown()
