import pytest
from forecast_engine.module_0106 import main_function, Module0106Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0106Error):
        main_function("not a list")
