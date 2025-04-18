import pytest
from strategic_interface.module_0057 import main_function, Module0057Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0057Error):
        main_function("not a list")
