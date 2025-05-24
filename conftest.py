import pytest


@pytest.fixture(scope="session")
def api_key():
    return "test_api_key_12345"
