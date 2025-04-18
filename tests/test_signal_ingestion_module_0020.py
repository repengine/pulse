import pytest
from signal_ingestion.module_0020 import main_function, Module0020Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0020Error):
        main_function("not a list")
