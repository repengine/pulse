import pytest
from simulation_engine.module_0099 import main_function, Module0099Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0099Error):
        main_function("not a list")
