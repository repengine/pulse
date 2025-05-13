import pytest

@pytest.fixture(scope="session")
def variable_name():
    return "test_variable"