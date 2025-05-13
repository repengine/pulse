import pytest

@pytest.fixture(scope="session")
def plugin_name():
    return "test_plugin"