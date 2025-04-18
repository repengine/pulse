import pytest
from simulation_engine.module_0002 import main_function, Module0002Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0002Error):
        main_function("not a list")
