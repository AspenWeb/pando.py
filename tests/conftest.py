from aspen.testing import teardown
from aspen.testing.pytest_fixtures import fs, harness, sys_path, module_scrubber
from aspen.testing.pytest_fixtures import sys_path_scrubber


def pytest_runtest_teardown():
    teardown()
