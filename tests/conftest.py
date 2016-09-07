from pando.testing.harness import teardown
from pando.testing.pytest_fixtures import (
    client, harness, fs, website, sys_path, sys_path_scrubber
)

client, harness, fs, website, sys_path, sys_path_scrubber  # shut up pyflakes

def pytest_runtest_teardown():
    teardown()
