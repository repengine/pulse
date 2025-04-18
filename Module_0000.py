"""
Module_0000: Example module with type hints and docstrings.
"""

from utils.file_utils import list_py_files

def example_function(directory: str) -> int:
    """
    Example function that counts Python files in a directory.

    Args:
        directory (str): Path to the directory.

    Returns:
        int: Number of Python files.
    """
    py_files = list_py_files(directory)
    return len(py_files)