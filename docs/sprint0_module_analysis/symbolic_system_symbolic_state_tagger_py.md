# Module Analysis: `symbolic_system/symbolic_state_tagger.py`

**Version:** `v0.30.1` (as per module docstring and metadata)
**Last Updated in Code:** 2025-04-16 (as per module docstring)

## 1. Module Intent/Purpose

The primary role of this module is to interpret current symbolic overlays (hope, despair, rage, fatigue) and assign a descriptive symbolic tag (e.g., "Hope Rising", "Collapse Risk") to represent the emotional state of a simulation. This tag is crucial for runtime narrative interpretation, symbolic trust scoring, forecast compression grouping, and strategic alignment interfaces.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope. It has a clear structure, input/output definitions, and logging. No obvious placeholders or major TODOs are visible in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility of Rules:** The decision rules for tagging are hardcoded in an `if/elif/else` structure. While functional, this could become cumbersome to manage or extend if more nuanced states or different overlay combinations are needed. A more data-driven or configurable rule system might be a logical next step for scalability.
*   **Advanced State Interpretation:** The current tagging is based on direct thresholds. Future enhancements could involve more complex pattern recognition over time or combinations of more symbolic overlays if the system evolves.
*   **No explicit signs of deviation:** The module seems to fulfill its stated purpose as of `v0.30.1`.

## 4. Connections & Dependencies

### Direct Project Imports
*   `from utils.log_utils import get_logger` ([`utils/log_utils.py:35`](../../../utils/log_utils.py:35))
*   `from core.path_registry import PATHS` ([`core/path_registry.py:36`](../../../core/path_registry.py:36))
*   `from forecast_output.forecast_tags import ForecastTag, get_tag_label` ([`forecast_output/forecast_tags.py:39`](../../../forecast_output/forecast_tags.py:39))

### External Library Dependencies
*   `os` (standard library)
*   `json` (standard library)
*   `datetime` (standard library)
*   `typing` (standard library, for `Dict`, `Optional`)

### Shared Data Interactions
*   Reads configuration from `PATHS` (likely defined in [`core/path_registry.py`](../../../core/path_registry.py)).
*   Uses `ForecastTag` enum and [`get_tag_label()`](../../../forecast_output/forecast_tags.py:39) function from [`forecast_output/forecast_tags.py`](../../../forecast_output/forecast_tags.py).

### Input/Output Files
*   **Output:** Writes logs to a JSONL file. The path is determined by `PATHS.get("SYMBOLIC_TAG_LOG", PATHS["WORLDSTATE_LOG_DIR"])`, typically resolving to `logs/symbolic_state_tags.jsonl`.

## 5. Function and Class Example Usages

### `tag_symbolic_state(overlays: Dict[str, float], sim_id: str = "default", turn: Optional[int] = None) -> Dict`
*   **Purpose:** Takes a dictionary of symbolic overlays, a simulation ID, and an optional turn number. It normalizes the overlays, applies a set of decision rules to determine a symbolic state tag (e.g., `HOPE`, `DESPAIR`), logs the result, and returns a dictionary containing the tag, overlays, timestamp, and metadata.
*   **Example (from module [`symbolic_system/symbolic_state_tagger.py:122`](../../../symbolic_system/symbolic_state_tagger.py:122)):**
    ```python
    example = tag_symbolic_state({
        "hope": 0.75,
        "despair": 0.2,
        "rage": 0.3,
        "fatigue": 0.25
    }, sim_id="v30_demo", turn=1)
    print(f"Symbolic Label: {example['symbolic_tag']}")
    ```

### `normalize_overlays(overlays: Dict[str, float]) -> Dict[str, float]`
*   **Purpose:** Ensures that the input `overlays` dictionary contains the keys "hope", "despair", "rage", and "fatigue", defaulting them to 0.5 if missing or invalid. It rounds the float values to 4 decimal places.
*   **Usage:** Called internally by [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:62).

### `ensure_log_dir(path: str)`
*   **Purpose:** Creates the directory for the log file if it doesn't exist. Silently handles `PermissionError` or other exceptions during directory creation.
*   **Usage:** Called internally by [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:62) before writing to the log file.

## 6. Hardcoding Issues

*   **Default Overlay Values:** In [`normalize_overlays()`](../../../symbolic_system/symbolic_state_tagger.py:54), the base values `{"hope": 0.5, "despair": 0.5, "rage": 0.5, "fatigue": 0.5}` are hardcoded.
*   **Decision Rule Thresholds:** The thresholds in the `if/elif` chain within [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:73) (e.g., `hope > 0.7`, `despair < 0.3`) are hardcoded.
*   **Version String:** `"v0.30.1"` is hardcoded in the metadata within [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:101) and in the module docstring.
*   **Source Filename:** `"symbolic_state_tagger.py"` is hardcoded in metadata ([`symbolic_system/symbolic_state_tagger.py:102`](../../../symbolic_system/symbolic_state_tagger.py:102)).
*   **Default Log Filename:** If `TAG_LOG_PATH` is a directory, `"symbolic_state_tags.jsonl"` is used as the default filename ([`symbolic_system/symbolic_state_tagger.py:111`](../../../symbolic_system/symbolic_state_tagger.py:111)).
*   **Default `sim_id`:** The `sim_id` parameter in [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:62) defaults to `"default"`.

## 7. Coupling Points

*   **`core.path_registry.PATHS`**: Tightly coupled for log path configuration. Changes to `PATHS` structure or keys like `SYMBOLIC_TAG_LOG` or `WORLDSTATE_LOG_DIR` would directly impact this module.
*   **`forecast_output.forecast_tags`**: Depends on `ForecastTag` enum and [`get_tag_label()`](../../../forecast_output/forecast_tags.py:39) function. Changes in these definitions would require updates.
*   **`utils.log_utils.get_logger`**: Standard logging dependency.
*   **Input Overlay Structure:** Expects `overlays` dictionary with specific keys ("hope", "despair", "rage", "fatigue"). Changes to these key names would break the tagging logic.

## 8. Existing Tests

*   The file list does not show a specific test file like `tests/symbolic_system/test_symbolic_state_tagger.py`.
*   The module includes an `if __name__ == "__main__":` block ([`symbolic_system/symbolic_state_tagger.py:121`](../../../symbolic_system/symbolic_state_tagger.py:121)) with a simple example usage, serving as a basic, informal test.
*   **Gaps:** Lack of dedicated unit tests means that edge cases, different combinations of overlay values, and the correctness of each rule branch are not systematically verified. Logging mechanism's error handling is also not explicitly tested.

## 9. Module Architecture and Flow

1.  **Initialization:** Sets up a logger and determines the log file path using `PATHS` from [`core.path_registry`](../../../core/path_registry.py).
2.  **Input:** The main function [`tag_symbolic_state()`](../../../symbolic_system/symbolic_state_tagger.py:62) receives symbolic `overlays`, `sim_id`, and `turn`.
3.  **Normalization:** [`normalize_overlays()`](../../../symbolic_system/symbolic_state_tagger.py:54) ensures required overlay keys exist and values are standardized.
4.  **Tagging Logic:** A series of `if/elif/else` conditions ([`symbolic_system/symbolic_state_tagger.py:73-89`](../../../symbolic_system/symbolic_state_tagger.py:73-89)) evaluate the normalized overlay values against predefined thresholds to select a `ForecastTag` enum member.
5.  **Label Retrieval:** [`get_tag_label()`](../../../forecast_output/forecast_tags.py:39) (from [`forecast_output.forecast_tags`](../../../forecast_output/forecast_tags.py)) converts the enum to a human-readable string.
6.  **Result Structuring:** A dictionary is created containing the simulation ID, turn, tag label, tag enum name, original overlays, timestamp, and metadata.
7.  **Logging:**
    *   [`ensure_log_dir()`](../../../symbolic_system/symbolic_state_tagger.py:45) creates the log directory if needed.
    *   The result dictionary is serialized to JSON and appended to the `symbolic_state_tags.jsonl` log file ([`symbolic_system/symbolic_state_tagger.py:107-116`](../../../symbolic_system/symbolic_state_tagger.py:107-116)). Errors during logging are caught and logged.
8.  **Output:** The structured result dictionary is returned.

## 10. Naming Conventions

*   **Functions:** `tag_symbolic_state`, `normalize_overlays`, `ensure_log_dir` follow `snake_case` (PEP 8).
*   **Variables:** Generally `snake_case` (e.g., `sim_id`, `log_path`).
*   **Constants:** `TAG_LOG_PATH` is `UPPER_SNAKE_CASE`. `PATHS` is also uppercase.
*   **Enums:** `ForecastTag` (imported) uses `PascalCase` for the enum name and `UPPER_SNAKE_CASE` for members.
*   **Clarity:** Names are descriptive and clear.
*   **AI Assumption Errors/Deviations:** No obvious AI assumption errors. Naming is consistent with Python best practices and PEP 8. The module header indicates authorship by "Pulse AI Engine," and conventions are sound.