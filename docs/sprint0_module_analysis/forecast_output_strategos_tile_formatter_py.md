# Module Analysis: `forecast_output/strategos_tile_formatter.py`

## 1. Module Intent/Purpose

The primary role of the [`forecast_output/strategos_tile_formatter.py`](forecast_output/strategos_tile_formatter.py:2) module is to take a structured forecast object (a Python dictionary) and format it into a "Strategos Forecast Tile". This tile is a compact, human-readable string representation designed to display key foresight information, including both symbolic (descriptive changes) and capital (financial asset changes) outcomes.

## 2. Operational Status/Completeness

The module appears to be **largely complete** for its defined purpose.
- It defines a single function, [`format_strategos_tile()`](forecast_output/strategos_tile_formatter.py:17), which performs the formatting.
- The formatting logic seems well-defined, extracting various pieces of information from the input `forecast_obj` and arranging them into a predefined string template.
- It includes logic to derive a "Trust Label" based on a `confidence` score.
- Default values are provided for many fields if they are missing from the input object (e.g., "N/A", "unscored", "unlabeled").

There are no obvious placeholders like "TODO" or "FIXME" comments in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Limited Scope of Capital Outcomes:** The "Exposure Delta" section currently hardcodes calculations for 'NVDA', 'MSFT', 'IBIT', and 'SPY' (lines 47-50). If the system is intended to handle forecasts for other or a dynamic set of capital assets, this section would need to be made more flexible, perhaps by iterating over available keys in `start_capital` and `end_capital` dictionaries.
- **Symbolic Change Detail:** The "Symbolic Drift" (line 53) simply displays `fc.get("symbolic_change")`. The nature and structure of this `symbolic_change` data are not clear from this module alone. If it's a complex object or a long string, its presentation here might be too simplistic or truncated. Further context on what `symbolic_change` contains would be needed to assess if its formatting is adequate.
- **Error Handling/Validation:** While default values are used for missing keys, there's no explicit error handling or validation for the *type* or *structure* of the input `forecast_obj` or its nested dictionaries beyond the `assert isinstance(PATHS, dict)` for a global configuration. If `forecast_obj` is malformed (e.g., `fc.get('end_capital')` is not a dictionary), the code could raise an `AttributeError`. More robust validation at the beginning of the function could be beneficial.
- **TILE_LOG_PATH Usage:** The module defines `TILE_LOG_PATH` (line 14) using `PATHS.get("TILE_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])` but this variable is not actually used within the module's code. This suggests an intended logging feature for these tiles might be missing or was planned and not implemented.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`core.path_registry.PATHS`](core/path_registry.py): Used to define `TILE_LOG_PATH`.

### External Library Dependencies:
- `typing.Dict`: Used for type hinting. This is a standard Python library.

### Interaction via Shared Data:
- **Input:** The module expects a `forecast_obj: Dict` as input to its main function. The structure of this dictionary is implicitly defined by the keys it attempts to access (e.g., `trace_id`, `origin_turn`, `forecast.end_capital.nvda`). This object is presumably generated by other parts of the "Pulse" system.
- **Output:** The module outputs a formatted string. The comment "Author: Pulse v3.5" suggests it's part of a larger system named Pulse.

### Input/Output Files:
- **Potentially Implied Log Files:** The unused `TILE_LOG_PATH` variable suggests that there might have been an intention to log the formatted tiles to a file, but this is not implemented in the current code. The path defaults to `PATHS["WORLDSTATE_LOG_DIR"]` if `TILE_LOG_PATH` is not in `PATHS`.

## 5. Function and Class Example Usages

The module contains one primary function:

### [`format_strategos_tile(forecast_obj: Dict) -> str`](forecast_output/strategos_tile_formatter.py:17)

**Purpose:** Formats a given forecast dictionary into a human-readable string tile.

**Intended Usage:**

```python
from forecast_output.strategos_tile_formatter import format_strategos_tile

# Example forecast_obj (structure inferred from the function)
sample_forecast = {
    "trace_id": "trace-123",
    "origin_turn": 5,
    "horizon_days": 30,
    "forecast": {
        "start_capital": {"nvda": 100.0, "msft": 200.0, "ibit": 50.0, "spy": 300.0},
        "end_capital": {"nvda": 110.0, "msft": 190.0, "ibit": 55.0, "spy": 305.0},
        "symbolic_change": "Market sentiment expected to improve slightly."
    },
    "alignment": {"some_alignment_metric": 0.8},
    "fragility": "Low",
    "confidence": 0.85, # Example: High confidence
    "status": "Reviewed",
    "age_hours": 2,
    "age_tag": "⚡️"
}

tile_string = format_strategos_tile(sample_forecast)
print(tile_string)

# Expected Output (structure):
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔮 Strategos Forecast Tile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Trace ID      : trace-123
# Turn          : 5
# Duration      : 30 days
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exposure Delta:
#   NVDA  → 10.00
#   MSFT  → -10.00
#   IBIT  → 5.00
#   SPY   → 5.00
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Symbolic Drift:
#   Market sentiment expected to improve slightly.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fragility     : Low
# Confidence    : 0.85
# Trust Label   : 🟢 Trusted
# Status        : Reviewed
# Age           : 2h ⚡️
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 6. Hardcoding Issues

- **Capital Asset Symbols (Lines 47-50):** The symbols 'NVDA', 'MSFT', 'IBIT', and 'SPY' are hardcoded for calculating "Exposure Delta". This limits the flexibility of the module to handle other assets without code modification.
- **Confidence Thresholds (Lines 28-34):** The thresholds for determining the "Trust Label" (0.75 for "Trusted", 0.5 for "Moderate") are hardcoded. These might be better defined as configurable constants if they are subject to change or tuning.
- **Default Strings/Emojis (various):** Strings like "N/A", "unscored", "unlabeled", and the age tag emoji "🕒" (though `age_tag` can be overridden by input) are hardcoded. This is generally acceptable for default display values but worth noting.
- **Tile Structure and Headings:** The entire string template with its "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" separators and headings like "🔮 Strategos Forecast Tile" is hardcoded. This is inherent to a formatter but means any structural change to the tile requires code modification.

## 7. Coupling Points

- **`core.path_registry.PATHS`:** The module is coupled to the structure and content of the `PATHS` dictionary from [`core.path_registry`](core/path_registry.py:11) for defining `TILE_LOG_PATH`. Changes to `PATHS` (e.g., key names) could break this module if not managed.
- **Input `forecast_obj` Structure:** The module is tightly coupled to the expected dictionary structure of `forecast_obj`. Any changes to the key names or data types within this object by upstream modules that generate it would require corresponding changes in this formatter. For example, it expects keys like `trace_id`, `origin_turn`, `forecast.start_capital.nvda`, etc.
- **Implicit Contract with Caller:** The caller of [`format_strategos_tile()`](forecast_output/strategos_tile_formatter.py:17) needs to ensure the `forecast_obj` adheres to the expected (though not formally defined) schema.

## 8. Existing Tests

- Based on the file listing from the `tests/` directory, there is no specific test file named `test_strategos_tile_formatter.py` or similar under `tests/` or a potential `tests/forecast_output/` subdirectory.
- A file named [`tests/test_strategos_digest_builder.py`](tests/test_strategos_digest_builder.py) exists, which might be related as it deals with "Strategos" and "digest", but it's unlikely to directly test this specific tile formatter.
- **Conclusion:** It appears there are **no dedicated unit tests** for the [`strategos_tile_formatter.py`](forecast_output/strategos_tile_formatter.py:2) module. This is a significant gap, as tests would be crucial for verifying the correct formatting output given various inputs, especially concerning the conditional logic for trust labels and calculations for exposure deltas.

## 9. Module Architecture and Flow

- **Architecture:** The module is very simple, consisting of a single Python file with one public function [`format_strategos_tile()`](forecast_output/strategos_tile_formatter.py:17). It also defines a module-level variable `TILE_LOG_PATH`.
- **Control Flow:**
    1. The [`format_strategos_tile(forecast_obj)`](forecast_output/strategos_tile_formatter.py:17) function is called with a dictionary.
    2. It extracts various values from the `forecast_obj` dictionary using `.get()` methods, providing defaults for missing keys.
    3. It computes a `label` string based on the `confidence` value.
    4. It calculates exposure deltas for hardcoded assets (NVDA, MSFT, IBIT, SPY) by subtracting start capital from end capital.
    5. It constructs and returns a multi-line f-string, embedding the extracted and computed values into a predefined tile format.
- **Data Flow:**
    - **Input:** `forecast_obj: Dict`.
    - **Processing:** Data is read from the input dictionary. Simple arithmetic is performed for capital deltas. Conditional logic determines the trust label.
    - **Output:** A formatted string.

## 10. Naming Conventions

- **Module Name (`strategos_tile_formatter.py`):** Clear and descriptive, following Python's snake_case convention.
- **Function Name (`format_strategos_tile`):** Clear, uses snake_case, and accurately describes its purpose.
- **Variable Names:**
    - `forecast_obj`, `f`, `fc`: Generally clear. `f` and `fc` are short aliases for `forecast_obj` and `forecast_obj.get("forecast", {})` respectively, which is acceptable within the function's scope for brevity.
    - `alignment`, `fragility`, `confidence`, `status`, `age`, `age_tag`, `label`: Clear and descriptive.
    - `TILE_LOG_PATH`: Uppercase with underscores, typical for constants, which is appropriate here.
- **Hardcoded Asset Keys ('nvda', 'msft', 'ibit', 'spy'):** These are lowercase, which is typical for dictionary keys.
- **Consistency:** Naming seems consistent and generally follows PEP 8 guidelines for Python.
- **Potential AI Assumption Errors:** The comment "Author: Pulse v3.5" (line 7) might be an AI-generated attribution or a placeholder; if this system is human-maintained, a specific author or team name might be more appropriate. However, this is a comment, not a code naming convention.

No obvious deviations from PEP 8 or significant AI assumption errors in naming conventions within the code itself are apparent. The hardcoded asset symbols are a design choice rather than a naming convention issue.