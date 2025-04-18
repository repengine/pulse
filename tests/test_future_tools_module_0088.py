import pytest
from future_tools.module_0088 import main_function, Module0088Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0088Error):
        main_function("not a list")
