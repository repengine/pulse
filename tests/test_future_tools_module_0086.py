import pytest
from future_tools.module_0086 import main_function, Module0086Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0086Error):
        main_function("not a list")
