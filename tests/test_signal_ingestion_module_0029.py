import pytest
from signal_ingestion.module_0029 import main_function, Module0029Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0029Error):
        main_function("not a list")
