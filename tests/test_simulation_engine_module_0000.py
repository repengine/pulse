import pytest
from simulation_engine.module_0000 import count_positive_numbers
from utils.error_utils import DataValidationError

def test_count_positive_numbers(sample_numbers):
    assert count_positive_numbers(sample_numbers) == 3

def test_count_positive_numbers_invalid():
    with pytest.raises(DataValidationError):
        count_positive_numbers("not a list")