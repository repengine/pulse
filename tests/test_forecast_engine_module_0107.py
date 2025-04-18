import pytest
from forecast_engine.module_0107 import main_function, Module0107Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0107Error):
        main_function("not a list")
