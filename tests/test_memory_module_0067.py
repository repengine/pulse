import pytest
from memory.module_0067 import main_function, Module0067Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0067Error):
        main_function("not a list")
