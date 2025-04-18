import pytest
from symbolic_system.module_0037 import main_function, Module0037Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0037Error):
        main_function("not a list")
