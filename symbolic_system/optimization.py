"""
optimization.py

Performance optimization utilities for the symbolic system, including:
- Caching mechanism for expensive symbolic computations
- Lazy evaluation decorators that respect system mode
- Training-specific processing optimizations

This module ensures the symbolic system adds minimal overhead,
especially during training/retrodiction operations.
"""

import functools
import time
import logging
from typing import Dict, Any, Callable, Optional, Tuple

# Import configuration
from core.pulse_config import (
    ENABLE_SYMBOLIC_SYSTEM, 
    CURRENT_SYSTEM_MODE,
    SYMBOLIC_PROCESSING_MODES
)

logger = logging.getLogger(__name__)

class SymbolicCache:
    """Cache for symbolic computations to avoid redundant processing"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        Initialize the cache with size and time-to-live limits.
        
        Args:
            max_size: Maximum number of entries in cache
            ttl_seconds: Time-to-live in seconds for cache entries
        """
        self.cache = {}  # Key -> Value
        self.timestamps = {}  # Key -> Timestamp
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Tuple[bool, Any]:
        """
        Get a value from cache if it exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Tuple of (found, value)
        """
        if key not in self.cache:
            self.misses += 1
            return False, None
            
        # Check if the entry has expired
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            del self.cache[key]
            del self.timestamps[key]
            self.misses += 1
            return False, None
            
        self.hits += 1
        return True, self.cache[key]
        
    def set(self, key: str, value: Any):
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
        """
        # If cache is full, remove oldest entry
        if len(self.cache) >= self.max_size:
            # Use lambda instead of .get method for better type compatibility
            oldest_key = min(self.timestamps, key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
            
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
    def clear(self):
        """Clear the cache"""
        self.cache = {}
        self.timestamps = {}
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "hit_rate": hit_rate,
            "hits": self.hits,
            "misses": self.misses
        }

# Create a singleton cache instance
# This will be shared across all symbolic computations
_symbolic_cache = SymbolicCache()

def get_symbolic_cache():
    """Get the singleton symbolic cache instance"""
    return _symbolic_cache

def cached_symbolic(ttl_seconds: int = 60):
    """
    Decorator for caching symbolic computation results.
    
    Args:
        ttl_seconds: Time-to-live in seconds for cache entries
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Only use cache if symbolic system is enabled
            if not ENABLE_SYMBOLIC_SYSTEM:
                return func(*args, **kwargs)
                
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            found, cached_result = _symbolic_cache.get(cache_key)
            if found:
                return cached_result
                
            # Compute and cache result
            result = func(*args, **kwargs)
            _symbolic_cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

def lazy_symbolic(func):
    """
    Decorator for lazy evaluation of symbolic computations.
    Skip execution entirely if symbolic processing is disabled.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with lazy evaluation
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get fresh values each time to ensure we have the latest values
        from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM as current_enable
        from core.pulse_config import CURRENT_SYSTEM_MODE as current_mode
        from core.pulse_config import SYMBOLIC_PROCESSING_MODES as current_modes
        
        # Skip evaluation if symbolic system is disabled
        if not current_enable:
            return None
            
        # Skip if in mode where symbolic processing is disabled
        if current_mode in current_modes and not current_modes[current_mode]:
            return None
            
        # Otherwise evaluate normally
        return func(*args, **kwargs)
    return wrapper

def training_optimized(default_value=None):
    """
    Decorator specifically for optimizing symbolic operations during training.
    Provides simplified execution in training modes.
    
    Args:
        default_value: Value to return in training mode
        
    Returns:
        Decorated function with training optimization
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get fresh values each time
            from core.pulse_config import CURRENT_SYSTEM_MODE as current_mode
            from core.pulse_config import SYMBOLIC_PROCESSING_MODES as current_modes
            
            # Use simplified execution in training/retrodiction mode
            if current_mode == "retrodiction":
                # Check if we should skip entirely
                if not current_modes.get("retrodiction", False):
                    return default_value
                
                # Otherwise use training-specific implementation if provided
                training_impl = kwargs.pop("training_impl", None)
                if training_impl and callable(training_impl):
                    return training_impl(*args, **kwargs)
            
            # Standard execution for non-training modes
            return func(*args, **kwargs)
        return wrapper
    return decorator

def is_expensive_operation() -> bool:
    """Check if we're in a mode where expensive operations should be avoided"""
    # Get fresh values
    from core.pulse_config import CURRENT_SYSTEM_MODE as current_mode
    
    expensive_modes = {"retrodiction", "training"}
    return current_mode in expensive_modes

def get_operation_level() -> str:
    """
    Get the appropriate operation level based on current mode.
    
    Returns:
        "full" - All operations
        "minimal" - Only essential operations
        "none" - No operations
    """
    # Get fresh values
    from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM as current_enable
    from core.pulse_config import CURRENT_SYSTEM_MODE as current_mode
    from core.pulse_config import SYMBOLIC_PROCESSING_MODES as current_modes
    
    if not current_enable:
        return "none"
        
    if current_mode == "retrodiction" and not current_modes.get("retrodiction", False):
        return "none"
        
    if current_mode in {"retrodiction", "training"}:
        return "minimal"
        
    return "full"