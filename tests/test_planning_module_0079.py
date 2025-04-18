import pytest
from planning.module_0079 import main_function, Module0079Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0079Error):
        main_function("not a list")
