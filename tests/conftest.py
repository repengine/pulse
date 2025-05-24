import pytest


@pytest.fixture
def sample_numbers():
    return [-2, 0, 3, 5, -1, 7]


# API-related fixtures


@pytest.fixture
def api_key():
    """
    Fixture providing a mock API key for testing API endpoints.

    This prevents tests from requiring actual API keys in the environment
    and standardizes the key used across all tests.
    """
    return "test_api_key_12345"


@pytest.fixture
def variable_name():
    """
    Fixture providing a standard variable name for API tests.

    This helps standardize the variable names used in tests and prevents
    tests from being dependent on specific variable configurations.
    """
    return "test_variable"


@pytest.fixture
def plugin_name():
    """
    Fixture providing a standard plugin name for plugin tests.

    This allows plugin tests to use a consistent plugin name without
    hard-coding the name in each test file.
    """
    return "test_plugin"
