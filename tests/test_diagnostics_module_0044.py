import pytest
from diagnostics.module_0044 import main_function, Module0044Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0044Error):
        main_function("not a list")
