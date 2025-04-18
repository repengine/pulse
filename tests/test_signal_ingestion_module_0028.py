import pytest
from signal_ingestion.module_0028 import main_function, Module0028Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0028Error):
        main_function("not a list")
