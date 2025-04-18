"""
Performance profiling utilities.
"""

import time
from functools import wraps

def profile(func):
    """
    Decorator to profile function execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} executed in {end - start:.6f}s")
        return result
    return wrapper