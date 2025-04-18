import pytest
from signal_ingestion.module_0022 import main_function, Module0022Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0022Error):
        main_function("not a list")
