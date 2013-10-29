from aspen.testing.fsfix import teardown
from aspen.testing.pytest_fixtures import fs, harness, sys_path, module_scrubber


def pytest_runtest_teardown():
    teardown()
