import pytest
from simulation_engine.module_0098 import main_function, Module0098Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0098Error):
        main_function("not a list")
