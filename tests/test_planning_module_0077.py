import pytest
from planning.module_0077 import main_function, Module0077Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0077Error):
        main_function("not a list")
