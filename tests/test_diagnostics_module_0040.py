import pytest
from diagnostics.module_0040 import main_function, Module0040Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0040Error):
        main_function("not a list")
