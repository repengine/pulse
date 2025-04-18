import pytest
from strategic_interface.module_0051 import main_function, Module0051Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0051Error):
        main_function("not a list")
