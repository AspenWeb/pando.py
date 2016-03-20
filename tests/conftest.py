from pando.testing.harness import teardown
from pando.testing.pytest_fixtures import client, harness, fs, website
from pando.testing.pytest_fixtures import sys_path, sys_path_scrubber


def pytest_runtest_teardown():
    teardown()
