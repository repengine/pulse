import pytest
from memory.module_0066 import main_function, Module0066Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0066Error):
        main_function("not a list")
