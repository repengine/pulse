"""
Common file utilities for Pulse modules.
"""

import os
from typing import List


def list_py_files(directory: str) -> List[str]:
    """
    List all Python files in a directory.
    """
    return [f for f in os.listdir(directory) if f.endswith(".py")]
