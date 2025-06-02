# Module Analysis: `symbolic_system/numeric_transforms.py`

## 1. Module Intent/Purpose

The primary role of the [`symbolic_system/numeric_transforms.py`](../../../symbolic_system/numeric_transforms.py) module is to provide bidirectional transformations between numeric indicators (statistical data) and symbolic overlay states. It aims to bridge the gap between quantitative data and qualitative symbolic representations, allowing the system to reason about numeric changes in symbolic terms and vice-versa.

Key functionalities include:
- Converting statistical indicators to symbolic overlay values (e.g., high volatility index to "fear").
- Mapping symbolic overlay states back to expected numeric impacts (e.g., "hope" overlay to an increase in price momentum).
- Tracking confidence scores for these transformations.
- Implementing adaptive thresholds for conversions, based on historical data.

## 2. Operational Status/Completeness

The module appears to be largely operational and relatively complete for its defined scope.
- It implements the core transformation logic for both `numeric_to_symbolic` and `symbolic_to_numeric` conversions.
- It includes a mechanism for loading, saving, and updating adaptive thresholds from/to a JSON file ([`config/adaptive_thresholds.json`](../../../config/adaptive_thresholds.json)).
- It maintains a history of transformations, potentially for learning or debugging.
- Confidence scoring is implemented.
- A singleton pattern is used to provide a global transformer instance via [`get_numeric_transformer()`](../../../symbolic_system/numeric_transforms.py:359).

There are no obvious `TODO` comments or major placeholders for core functionality within the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Extensibility of Mappings:** While the module has default mappings for common indicators (e.g., "volatility_index", "price_momentum") and can load variable-specific mappings from a configuration (via [`get_symbolic_config()`](../../../symbolic_system/config.py:0)), the mechanism for defining and managing a large, evolving set of these mappings isn't fully detailed. The current implementation relies on hardcoded default logic if specific configurations are not found.
- **Learning/Refinement of Transformations:** The module stores `transformation_history` and updates `confidence_scores` (lines [`285-291`](../../../symbolic_system/numeric_transforms.py:285-291)). However, how this history is actively used for learning or refining the transformation logic or confidence scores beyond simple averaging is not explicitly implemented within this module. It suggests an intention for a more sophisticated learning loop that might reside elsewhere or is a planned future enhancement.
- **Dynamic Overlay Creation:** The [`apply_numeric_to_state()`](../../../symbolic_system/numeric_transforms.py:293) method has logic to create new "secondary" overlays if a transformation results in a high-confidence mapping to an overlay not yet present in the `WorldState` (lines [`311-320`](../../../symbolic_system/numeric_transforms.py:311-320)). The management and lifecycle of these dynamically created overlays could be an area for further development (e.g., pruning, promotion to primary).
- **Sophistication of `symbolic_to_numeric`:** The [`symbolic_to_numeric()`](../../../symbolic_system/numeric_transforms.py:162) mapping is currently a set of fixed rules. A more advanced system might learn these impacts or allow for more complex, context-dependent relationships. The check `if overlay_name in ["hope", "despair", "rage", "fatigue", "trust"]:` followed by `return {}` on line [`214`](../../../symbolic_system/numeric_transforms.py:214) seems redundant as these cases are handled above; this might be a remnant of a previous logic or an incomplete refactoring.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`logging`](https://docs.python.org/3/library/logging.html): Standard Python library.
- [`numpy`](https://numpy.org/) (as `np`): External library.
- [`json`](https://docs.python.org/3/library/json.html): Standard Python library.
- [`os`](https://docs.python.org/3/library/os.html): Standard Python library.
- `typing` (`Dict`, `List`, `Tuple`, `Optional`, `Any`): Standard Python library.
- `datetime` (`datetime`, `timedelta`): Standard Python library.
- [`engine.worldstate.WorldState`](../../../simulation_engine/worldstate.py:0), [`engine.worldstate.SymbolicOverlays`](../../../simulation_engine/worldstate.py:0): For interacting with the system's state representation.
- [`symbolic_system.optimization.cached_symbolic`](../../../symbolic_system/optimization.py:0): A custom decorator for caching results.
- [`symbolic_system.config.get_symbolic_config`](../../../symbolic_system/config.py:0): For fetching configuration related to symbolic mappings.

### External Library Dependencies:
- `numpy`: Used for numerical operations, particularly in [`update_adaptive_thresholds()`](../../../symbolic_system/numeric_transforms.py:220) (e.g., `np.mean`, `np.std`, `np.percentile`).

### Interaction with Other Modules via Shared Data:
- **Configuration Files:**
    - Reads variable-specific mappings via [`get_symbolic_config()`](../../../symbolic_system/config.py:0), implying it interacts with a configuration system defined in [`symbolic_system.config`](../../../symbolic_system/config.py:0).
    - Loads and saves adaptive thresholds and historical statistics to [`config/adaptive_thresholds.json`](../../../config/adaptive_thresholds.json) (relative to the `symbolic_system` directory, so likely `symbolic_system/config/adaptive_thresholds.json`).
- **WorldState Object:** The [`apply_numeric_to_state()`](../../../symbolic_system/numeric_transforms.py:293) method directly modifies `SymbolicOverlays` within a passed `WorldState` object.

### Input/Output Files:
- **Input/Output:** [`config/adaptive_thresholds.json`](../../../config/adaptive_thresholds.json) is read from and written to by the [`_load_thresholds()`](../../../symbolic_system/numeric_transforms.py:50) and [`_save_thresholds()`](../../../symbolic_system/numeric_transforms.py:62) methods.
- **Logs:** Uses the `logging` module to output informational messages and errors.

## 5. Function and Class Example Usages

### `SymbolicNumericTransformer` Class

```python
from symbolic_system.numeric_transforms import get_numeric_transformer
from engine.worldstate import WorldState # Assuming WorldState is properly importable

# Get the singleton transformer instance
transformer = get_numeric_transformer()

# Example 1: Convert numeric indicator to symbolic
indicator_name = "volatility_index"
numeric_value = 30.0
overlay_name, overlay_value, confidence = transformer.numeric_to_symbolic(indicator_name, numeric_value)
# Expected: overlay_name might be "fear", overlay_value > 0.5, confidence around 0.8

print(f"Numeric {indicator_name}={numeric_value} -> Symbolic {overlay_name}={overlay_value:.2f} (Confidence: {confidence:.2f})")

# Example 2: Convert symbolic overlay to numeric impacts
symbolic_overlay = "hope"
symbolic_value = 0.8 # Strong hope
numeric_impacts = transformer.symbolic_to_numeric(symbolic_overlay, symbolic_value)
# Expected: numeric_impacts might include {'price_momentum': positive_value, 'volatility_index': low_value}

print(f"Symbolic {symbolic_overlay}={symbolic_value} -> Numeric Impacts: {numeric_impacts}")

# Example 3: Update adaptive thresholds
historical_data = {
    "volatility_index": [10, 12, 15, 20, 25, 22, 18, 30, 35, 28],
    "price_momentum": [-0.5, 0.2, 1.0, 0.8, -0.1, 0.5, 1.2, 1.5, 0.3, -0.3]
}
transformer.update_adaptive_thresholds(historical_data)
# This will update self.adaptive_thresholds and save to 'adaptive_thresholds.json'

# Example 4: Apply numeric indicators to a WorldState
current_world_state = WorldState() # Initialize or get a WorldState instance
# Initialize some overlays if they don't exist or rely on dynamic creation
current_world_state.overlays.add_overlay("fear", 0.5)
current_world_state.overlays.add_overlay("confidence", 0.5)


current_indicators = {
    "volatility_index": 28.0,
    "price_momentum": -0.5
}
applied_transformations = transformer.apply_numeric_to_state(current_world_state, current_indicators)

print(f"Applied transformations: {applied_transformations}")
print(f"Updated WorldState overlays: Fear={current_world_state.overlays.fear:.2f}, Confidence={current_world_state.overlays.confidence:.2f}")

# Example 5: Get confidence for an overlay
fear_confidence = transformer.get_confidence("fear")
print(f"Overall confidence for 'fear' overlay: {fear_confidence:.2f}")
```

## 6. Hardcoding Issues

- **Default Thresholds and Mappings:**
    - In [`numeric_to_symbolic()`](../../../symbolic_system/numeric_transforms.py:82):
        - `volatility_index` / `vix`: `thresh_high` defaults to `25`, `thresh_low` to `15` if not in `adaptive_thresholds`. The scaling factors (e.g., `/ 20`, `/ 10`) are hardcoded.
        - `price_momentum`: Scaling factor `/ 10` is hardcoded.
        - `rsi` / `strength`: Thresholds `70` and `30` are standard but hardcoded, scaling `/ 30`.
        - `trend`: Thresholds `0.7` and `0.3` and scaling factors are hardcoded.
        - Default confidence values (e.g., `0.8`, `0.7`, `0.75`, `0.6`, `0.3`) are hardcoded for various rules.
    - In [`symbolic_to_numeric()`](../../../symbolic_system/numeric_transforms.py:162):
        - The impact multipliers (e.g., `0.5`, `0.3`, `0.2`, `0.4`, `10`, `15`, `20`) are hardcoded for each overlay-to-indicator mapping.
- **File Path Construction:**
    - `self.threshold_file = os.path.join(os.path.dirname(__file__), "..", "config", "adaptive_thresholds.json")` (line [`46`](../../../symbolic_system/numeric_transforms.py:46-47)). While using `os.path.join` is good, the relative path `"..", "config", "adaptive_thresholds.json"` assumes a specific directory structure relative to `numeric_transforms.py`. This could be made more robust via a centralized configuration path manager if the project structure changes.
- **Transformation History Size:**
    - `if len(self.transformation_history) > 1000:` (line [`282`](../../../symbolic_system/numeric_transforms.py:282)) - the maximum history size `1000` is hardcoded.
- **Confidence Update Factor:**
    - `self.confidence_scores[key] = 0.9 * self.confidence_scores[key] + 0.1 * confidence` (line [`291`](../../../symbolic_system/numeric_transforms.py:291)) - the learning rate/smoothing factor `0.1` (and `0.9`) is hardcoded.
- **Influence Weight Calculation:**
    - `influence_weight = min(0.2, confidence / 5)` (line [`327`](../../../symbolic_system/numeric_transforms.py:327)) - the cap `0.2` and divisor `5` are hardcoded.
- **Core Overlay Names:** The list `["hope", "despair", "rage", "fatigue", "trust"]` is used multiple times (e.g. lines [`214`](../../../symbolic_system/numeric_transforms.py:214), [`313`](../../../symbolic_system/numeric_transforms.py:313)) and could be a constant.

## 7. Coupling Points

- **`SymbolicNumericTransformer` and `symbolic_system.config`:** Tightly coupled for fetching variable-specific mappings. Changes in the config structure or access method would require changes here.
- **`SymbolicNumericTransformer` and `engine.worldstate`:** The transformer directly interacts with `WorldState` and `SymbolicOverlays` objects, particularly in [`apply_numeric_to_state()`](../../../symbolic_system/numeric_transforms.py:293). Changes to the `WorldState` or `SymbolicOverlays` API could impact this module.
- **`SymbolicNumericTransformer` and `adaptive_thresholds.json`:** The structure of this JSON file is implicitly defined by [`_load_thresholds()`](../../../symbolic_system/numeric_transforms.py:50) and [`_save_thresholds()`](../../../symbolic_system/numeric_transforms.py:62). Changes to the file format would break these methods.
- **`cached_symbolic` decorator:** The module relies on this decorator from [`symbolic_system.optimization`](../../../symbolic_system/optimization.py:0). Its behavior (caching, TTL) influences the performance and freshness of transformations.

## 8. Existing Tests

Based on the `list_files` result for `tests/symbolic_system/`, there is no specific test file like `test_numeric_transforms.py`. The directory contains:
- [`__init__.py`](../../../tests/symbolic_system/__init__.py:0)
- `gravity/` (a subdirectory, likely for testing the `gravity` sub-package)

This indicates a **gap in dedicated unit tests** for the `SymbolicNumericTransformer` class and its methods. While integration tests elsewhere might cover some functionality, specific unit tests for transformation logic, threshold updates, and confidence scoring are advisable.

## 9. Module Architecture and Flow

- **Singleton Pattern:** The module uses a global singleton `_transformer_instance` for [`SymbolicNumericTransformer`](../../../symbolic_system/numeric_transforms.py:27), accessible via [`get_numeric_transformer()`](../../../symbolic_system/numeric_transforms.py:359). This ensures a single, consistent source for transformations and state (like adaptive thresholds).
- **`SymbolicNumericTransformer` Class:**
    - **Initialization (`__init__`)**: Sets up storage for confidence scores, historical stats, adaptive thresholds, and transformation history. Loads thresholds from a file.
    - **Threshold Management (`_load_thresholds`, `_save_thresholds`, `update_adaptive_thresholds`)**: Handles persistence and dynamic adjustment of thresholds based on historical data.
    - **Core Transformation Logic:**
        - [`numeric_to_symbolic()`](../../../symbolic_system/numeric_transforms.py:82): Takes a numeric indicator and its value, consults configuration or default rules, and returns a symbolic overlay name, its value, and a confidence score.
        - [`symbolic_to_numeric()`](../../../symbolic_system/numeric_transforms.py:162): Takes a symbolic overlay and its value, and returns a dictionary of expected impacts on numeric indicators.
    - **State Interaction (`apply_numeric_to_state`)**: Iterates through provided numeric indicators, transforms them to symbolic values, and updates a `WorldState` object's overlays based on these transformations and their confidence.
    - **Learning/Tracking (`_record_transformation`, `get_confidence`)**: Records each transformation and updates/retrieves confidence scores.
- **Caching:** The [`@cached_symbolic`](../../../symbolic_system/optimization.py:0) decorator is applied to [`numeric_to_symbolic()`](../../../symbolic_system/numeric_transforms.py:82) and [`symbolic_to_numeric()`](../../../symbolic_system/numeric_transforms.py:162), suggesting that results of these potentially expensive or frequently called transformations are cached for a period (TTL 300 seconds).

**Primary Data Flow:**
1.  Numeric data (indicators) comes in.
2.  [`numeric_to_symbolic()`](../../../symbolic_system/numeric_transforms.py:82) converts it to symbolic states using adaptive thresholds and configured/default rules.
3.  These symbolic states can update a `WorldState` via [`apply_numeric_to_state()`](../../../symbolic_system/numeric_transforms.py:293).
4.  Conversely, symbolic states can be translated back to expected numeric impacts via [`symbolic_to_numeric()`](../../../symbolic_system/numeric_transforms.py:162).
5.  Historical data can be fed into [`update_adaptive_thresholds()`](../../../symbolic_system/numeric_transforms.py:220) to refine the numeric-to-symbolic conversion logic.
6.  All transformations are recorded, and confidence scores are maintained.

## 10. Naming Conventions

- **Class Name:** [`SymbolicNumericTransformer`](../../../symbolic_system/numeric_transforms.py:27) is clear and follows PascalCase (PEP 8).
- **Method Names:** Generally follow snake_case (PEP 8), e.g., [`numeric_to_symbolic()`](../../../symbolic_system/numeric_transforms.py:82), [`_load_thresholds()`](../../../symbolic_system/numeric_transforms.py:50).
- **Variable Names:** Mostly use snake_case, e.g., `indicator_name`, `overlay_value`.
- **Constants/Globals:** `_transformer_instance` uses a leading underscore, typical for internal module globals.
- **Clarity:** Names are generally descriptive (e.g., `historical_stats`, `adaptive_thresholds`).
- **Potential AI Assumption Errors/Deviations:**
    - The term "overlay_name" and "overlay_value" are consistent.
    - Indicator names like "volatility_index", "price_momentum" are descriptive.
    - The symbolic states ("hope", "despair", "fear", "confidence", "fatigue", "trust", "rage") are evocative, though their precise meaning and interrelation would be defined by the broader symbolic system.
    - No obvious AI-like naming errors (e.g., overly generic or nonsensical names) are apparent. The naming seems human-generated and domain-specific.
- **PEP 8 Adherence:** The module largely adheres to PEP 8 naming conventions.

One minor point: the `cached_symbolic` decorator is used, which is specific to this project. Its naming is consistent with the module's theme.