import pytest
from future_tools.module_0085 import main_function, Module0085Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0085Error):
        main_function("not a list")
