import pytest
from signal_ingestion.module_0025 import main_function, Module0025Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0025Error):
        main_function("not a list")
