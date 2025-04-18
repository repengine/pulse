import pytest
from symbolic_system.module_0032 import main_function, Module0032Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0032Error):
        main_function("not a list")
