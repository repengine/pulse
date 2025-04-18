import pytest
from simulation_engine.module_0095 import main_function, Module0095Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module0095Error):
        main_function("not a list")
