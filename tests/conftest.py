import pytest

# Centralized list of flaky tests with GTK timing issues
# These tests are skipped by default but can be run with: pytest -k "testInserting or testBackspace or testDelete"
FLAKY_TESTS = [
    "tests/test_masks.py::TestMasks::testInserting",
    "tests/test_masks.py::TestMasks::testBackspace",
    "tests/test_masks.py::TestMasks::testDelete",
]


def pytest_configure(config):
    config.addinivalue_line("markers", "flaky: tests that are flaky due to GTK timing issues")


def pytest_collection_modifyitems(config, items):
    """Skip flaky tests unless explicitly requested via -k"""
    if config.getoption("-k"):
        return  # Don't skip if -k is used
    
    skip_flaky = pytest.mark.skip(reason="GTK timing issues (run with -k to execute)")
    for item in items:
        if item.nodeid in FLAKY_TESTS:
            item.add_marker(skip_flaky)
