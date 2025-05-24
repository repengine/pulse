"""
Performance profiling utilities for Pulse modules.
Provides decorators and tools for measuring and reporting execution time.
"""

import time
from functools import wraps
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def profile(func):
    """
    Decorator to profile function execution time and log the result.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start
        logger.info(f"[PROFILE] {func.__name__} executed in {duration:.6f}s")
        return result

    return wrapper


def timeit(label: Optional[str] = None):
    """
    Decorator to time a function and print/log the result with a custom label.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            duration = end - start
            msg = f"[TIMEIT] {label or func.__name__} took {duration:.6f}s"
            logger.info(msg)
            return result

        return wrapper

    return decorator


def profile_block(label: Optional[str] = None):
    """
    Context manager for profiling a code block.
    Usage:
        with profile_block("my_block"):
            ...
    """
    from contextlib import contextmanager

    @contextmanager
    def _profile_block():
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        msg = f"[PROFILE_BLOCK] {label or 'block'} executed in {end - start:.6f}s"
        logger.info(msg)

    return _profile_block()
