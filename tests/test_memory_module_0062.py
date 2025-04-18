import pytest
from memory.module_0062 import main_function, Module0062Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0062Error):
        main_function("not a list")
