# Module Analysis: `symbolic_system/optimization.py`

## 1. Module Intent/Purpose

The primary role of [`symbolic_system/optimization.py`](symbolic_system/optimization.py) is to provide performance optimization utilities for the symbolic system. This includes mechanisms for caching expensive symbolic computations, decorators for lazy evaluation that respect the current system mode, and training-specific processing optimizations. The goal is to minimize the overhead introduced by the symbolic system, particularly during resource-intensive operations like training and retrodiction.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It implements a [`SymbolicCache`](symbolic_system/optimization.py:27) class with `max_size` and `ttl_seconds` parameters.
- It provides decorators: [`cached_symbolic`](symbolic_system/optimization.py:112), [`lazy_symbolic`](symbolic_system/optimization.py:147), and [`training_optimized`](symbolic_system/optimization.py:177).
- Helper functions like [`is_expensive_operation`](symbolic_system/optimization.py:211) and [`get_operation_level`](symbolic_system/optimization.py:219) are present.
- There are no obvious placeholders (e.g., `pass`, `NotImplementedError`) or TODO comments within the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Training-Specific Implementation Details:** The [`training_optimized`](symbolic_system/optimization.py:177) decorator allows for a `training_impl` callable to be passed via `kwargs`. While the mechanism is there, the module itself doesn't define or suggest specific alternative implementations for training. These would likely reside in the modules/functions that *use* this decorator.
- **Cache Persistence:** The current [`SymbolicCache`](symbolic_system/optimization.py:27) is in-memory and transient. For longer-running processes or across restarts, a persistent cache (e.g., disk-based or using a dedicated cache server) might be a logical extension if cache warm-up time becomes significant.
- **Advanced Cache Eviction Strategies:** The cache uses a simple "remove oldest entry" when full, based on insertion timestamp. More sophisticated strategies (LRU, LFU) could be considered if cache performance becomes a bottleneck, though the current approach is reasonable for many use cases.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:
- [`core.pulse_config`](core/pulse_config.py): Imports `ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, `SYMBOLIC_PROCESSING_MODES`. These are crucial for controlling the behavior of the optimization utilities based on global system state.

### External Library Dependencies:
- `functools`: Used for [`@functools.wraps`](https://docs.python.org/3/library/functools.html#functools.wraps) in decorators to preserve metadata of the wrapped functions.
- `time`: Used for managing timestamps in the [`SymbolicCache`](symbolic_system/optimization.py:27) for TTL (time-to-live) functionality.
- `logging`: Used for standard logging.

### Interaction with Other Modules via Shared Data:
- The module provides a singleton cache instance ([`_symbolic_cache`](symbolic_system/optimization.py:106)) accessible via [`get_symbolic_cache()`](symbolic_system/optimization.py:108). Other parts of the symbolic system would interact with this module by using this shared cache (implicitly through decorators or explicitly).
- Configuration values from [`core.pulse_config`](core/pulse_config.py) (like `CURRENT_SYSTEM_MODE`) are read to dynamically adjust behavior.

### Input/Output Files:
- The module itself does not directly read from or write to files, other than potentially logging output if configured at a higher level.

## 5. Function and Class Example Usages

### [`SymbolicCache`](symbolic_system/optimization.py:27)
```python
# Get the global cache instance
cache = get_symbolic_cache()

# Set a value
cache.set("my_key", {"data": "some_value"})

# Get a value
found, value = cache.get("my_key")
if found:
    print(f"Cache hit: {value}")
else:
    print("Cache miss")

# Get stats
stats = cache.get_stats()
print(f"Cache size: {stats['size']}, Hit rate: {stats['hit_rate']:.2f}")
```

### [`@cached_symbolic(ttl_seconds=300)`](symbolic_system/optimization.py:112)
```python
from symbolic_system.optimization import cached_symbolic, get_symbolic_cache
from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM # Assuming this is set

# ENABLE_SYMBOLIC_SYSTEM = True # For example

@cached_symbolic(ttl_seconds=300)
def expensive_computation(param1, param2):
    print(f"Performing expensive computation with {param1}, {param2}")
    # Simulate work
    time.sleep(1)
    return param1 + param2

# First call: computes and caches
result1 = expensive_computation(10, 20) # "Performing expensive computation..." will print
print(f"Result 1: {result1}")

# Second call with same args: retrieves from cache
result2 = expensive_computation(10, 20) # "Performing expensive computation..." will NOT print
print(f"Result 2: {result2}")

# After TTL expires, or with different args, it would recompute.
```

### [`@lazy_symbolic`](symbolic_system/optimization.py:147)
```python
from symbolic_system.optimization import lazy_symbolic
# Assuming core.pulse_config.ENABLE_SYMBOLIC_SYSTEM and CURRENT_SYSTEM_MODE are set appropriately

@lazy_symbolic
def symbolic_only_task(data):
    print(f"Performing symbolic-only task with {data}")
    return f"Processed {data}"

# If ENABLE_SYMBOLIC_SYSTEM is False, or if CURRENT_SYSTEM_MODE is one where
# symbolic processing is disabled in SYMBOLIC_PROCESSING_MODES,
# symbolic_only_task(my_data) will return None without printing.
# Otherwise, it executes normally.
result = symbolic_only_task("example_data")
if result:
    print(result)
```

### [`@training_optimized(default_value="optimized_out")`](symbolic_system/optimization.py:177)
```python
from symbolic_system.optimization import training_optimized
# Assuming core.pulse_config.CURRENT_SYSTEM_MODE is set

def my_training_specific_logic(arg1):
    return f"Simplified training logic for {arg1}"

@training_optimized(default_value="skipped_in_training")
def complex_symbolic_function(arg1, training_impl=None): # training_impl is picked up by decorator
    print(f"Running full complex_symbolic_function with {arg1}")
    return f"Full result for {arg1}"

# Example:
# from core.pulse_config import CURRENT_SYSTEM_MODE, SYMBOLIC_PROCESSING_MODES
# CURRENT_SYSTEM_MODE = "retrodiction"
# SYMBOLIC_PROCESSING_MODES["retrodiction"] = True # Enable for retrodiction

# If CURRENT_SYSTEM_MODE is "retrodiction":
# 1. If SYMBOLIC_PROCESSING_MODES["retrodiction"] is False:
#    result = complex_symbolic_function("data") # result will be "skipped_in_training"
# 2. If SYMBOLIC_PROCESSING_MODES["retrodiction"] is True and training_impl is passed:
#    result = complex_symbolic_function("data", training_impl=my_training_specific_logic)
#    # result will be "Simplified training logic for data"
# 3. If SYMBOLIC_PROCESSING_MODES["retrodiction"] is True and no training_impl:
#    result = complex_symbolic_function("data")
#    # result will be "Full result for data" (falls back to original func)

# If CURRENT_SYSTEM_MODE is "normal_operation":
# result = complex_symbolic_function("data") # Runs full function
# print(result)
```

### [`is_expensive_operation()`](symbolic_system/optimization.py:211)
```python
# from core.pulse_config import CURRENT_SYSTEM_MODE
# CURRENT_SYSTEM_MODE = "retrodiction"
if is_expensive_operation():
    print("Currently in a mode where expensive operations should be avoided (e.g., training, retrodiction).")
else:
    print("Not in an expensive operation mode.")
```

### [`get_operation_level()`](symbolic_system/optimization.py:219)
```python
# from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM, CURRENT_SYSTEM_MODE, SYMBOLIC_PROCESSING_MODES
# ENABLE_SYMBOLIC_SYSTEM = True
# CURRENT_SYSTEM_MODE = "training"
# SYMBOLIC_PROCESSING_MODES["training"] = True

level = get_operation_level()
print(f"Current symbolic operation level: {level}")
# Possible outputs: "full", "minimal", "none"
```

## 6. Hardcoding Issues

- **Cache Defaults:** The [`SymbolicCache`](symbolic_system/optimization.py:27) constructor has default values for `max_size` (1000) and `ttl_seconds` (300). While these are defaults and can be overridden if the cache were instantiated differently, the singleton `_symbolic_cache` uses these defaults. If these need to be configurable system-wide, they should ideally be sourced from [`core.pulse_config`](core/pulse_config.py).
- **Decorator Default TTL:** The [`cached_symbolic`](symbolic_system/optimization.py:112) decorator has a default `ttl_seconds` of 60. This is a reasonable default but acts as a hardcoded value if not specified at the decoration site.
- **Expensive Modes List:** The function [`is_expensive_operation`](symbolic_system/optimization.py:211) contains a hardcoded set `expensive_modes = {"retrodiction", "training"}` ([`symbolic_system/optimization.py:216`](symbolic_system/optimization.py:216)). If new modes are added that should also be considered "expensive," this set would need manual updating. This could potentially be driven by `SYMBOLIC_PROCESSING_MODES` if its structure allowed for such a distinction.
- **Operation Level Logic:** The logic within [`get_operation_level`](symbolic_system/optimization.py:219) for determining "minimal" vs "full" based on `current_mode` also uses the hardcoded set `{"retrodiction", "training"}` ([`symbolic_system/optimization.py:239`](symbolic_system/optimization.py:239)).

## 7. Coupling Points

- **Strong Coupling to [`core.pulse_config`](core/pulse_config.py):** The module's behavior is heavily dependent on configuration values (`ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, `SYMBOLIC_PROCESSING_MODES`) imported from [`core.pulse_config`](core/pulse_config.py). Changes to the names, structure, or meaning of these config variables would directly impact this module. The local re-imports within functions ([`lazy_symbolic`](symbolic_system/optimization.py:160-163), [`training_optimized`](symbolic_system/optimization.py:192-193), [`is_expensive_operation`](symbolic_system/optimization.py:214), [`get_operation_level`](symbolic_system/optimization.py:229-231)) are a strategy to ensure fresh values but highlight this tight coupling.
- **Global Cache Instance:** The singleton `_symbolic_cache` ([`symbolic_system/optimization.py:106`](symbolic_system/optimization.py:106)) creates a global state. Any module using the caching decorators or [`get_symbolic_cache()`](symbolic_system/optimization.py:108) will share this instance, making them implicitly coupled through this shared resource. Cache key collisions could occur if not carefully managed (though the current key generation strategy including function name and arguments mitigates this for decorated functions).

## 8. Existing Tests

- To assess existing tests, one would typically look for a corresponding test file, such as `tests/symbolic_system/test_optimization.py`.
- Based on the provided file list, there is no direct `test_optimization.py` under `tests/symbolic_system/`.
- There is a `tests/symbolic_system/gravity/__init__.py` and `tests/symbolic_system/gravity/test_residual_gravity_engine.py`, but these do not seem directly relevant to testing the optimization utilities themselves.
- **Conclusion:** There are no apparent dedicated tests for this module in the provided file structure. Testing would be crucial for:
    - Cache logic (hits, misses, TTL, eviction).
    - Correct behavior of decorators under different `core.pulse_config` settings.
    - Cache key generation to ensure uniqueness and correctness.

## 9. Module Architecture and Flow

- **Singleton Cache:** The core is the [`SymbolicCache`](symbolic_system/optimization.py:27) class, with a global singleton instance ([`_symbolic_cache`](symbolic_system/optimization.py:106)) used by default.
- **Decorators:** Three primary decorators ([`cached_symbolic`](symbolic_system/optimization.py:112), [`lazy_symbolic`](symbolic_system/optimization.py:147), [`training_optimized`](symbolic_system/optimization.py:177)) wrap functions to modify their behavior.
    - They read global configuration from [`core.pulse_config`](core/pulse_config.py) to decide whether/how to execute the wrapped function or use the cache.
- **Helper Functions:** [`is_expensive_operation()`](symbolic_system/optimization.py:211) and [`get_operation_level()`](symbolic_system/optimization.py:219) also read global configuration to provide status information that other parts of the system might use to tailor behavior.
- **Control Flow:**
    - Decorators intercept function calls.
    - Based on `ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, and `SYMBOLIC_PROCESSING_MODES`:
        - Caching may be bypassed or utilized.
        - Function execution may be skipped entirely (lazy evaluation).
        - Alternative implementations or default values may be returned (training optimization).
    - The cache itself uses timestamps for TTL and a basic size limit eviction.

## 10. Naming Conventions

- **Classes:** [`SymbolicCache`](symbolic_system/optimization.py:27) uses CapWords (PascalCase), which is standard (PEP 8).
- **Functions and Methods:** `get_symbolic_cache`, `cached_symbolic`, `lazy_symbolic`, `training_optimized`, `is_expensive_operation`, `get_operation_level`, `get`, `set`, `clear`, `get_stats` use snake_case, which is standard (PEP 8).
- **Variables:** `max_size`, `ttl_seconds`, `cache_key`, `default_value`, `expensive_modes` use snake_case.
- **Private/Internal:** `_symbolic_cache` uses a single leading underscore, conventionally indicating it's for internal use.
- **Constants (from import):** `ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, `SYMBOLIC_PROCESSING_MODES` are all uppercase, which is standard for constants.
- **Local Re-imports for Freshness:** Variables like `current_enable`, `current_mode`, `current_modes` within functions ([`lazy_symbolic`](symbolic_system/optimization.py:161-163)) are named clearly.
- **Consistency:** Naming is generally consistent and follows Python conventions (PEP 8). No obvious AI assumption errors or significant deviations are noted. The use of `key=lambda k: self.timestamps[k]` ([`symbolic_system/optimization.py:80`](symbolic_system/optimization.py:80)) instead of `self.timestamps.get` for `min()` is a good detail for type compatibility and correctness.