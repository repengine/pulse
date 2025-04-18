import pytest
from planning.module_0072 import main_function, Module0072Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0072Error):
        main_function("not a list")
