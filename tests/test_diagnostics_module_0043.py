import pytest
from diagnostics.module_0043 import main_function, Module0043Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0043Error):
        main_function("not a list")
