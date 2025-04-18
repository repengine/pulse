"""
Simulation Engine Module 0000: Example with logging, error handling, and type hints.
"""

from utils.log_utils import get_logger
from utils.error_utils import DataValidationError

logger = get_logger(__name__)

def count_positive_numbers(numbers: list[int]) -> int:
    """
    Counts positive numbers in a list.

    Args:
        numbers (list[int]): List of integers.

    Returns:
        int: Number of positive integers.

    Raises:
        DataValidationError: If input is not a list of integers.
    """
    if not isinstance(numbers, list) or not all(isinstance(n, int) for n in numbers):
        logger.error("Input must be a list of integers.")
        raise DataValidationError("Input must be a list of integers.")
    count = sum(1 for n in numbers if n > 0)
    logger.info(f"Counted {count} positive numbers.")
    return count