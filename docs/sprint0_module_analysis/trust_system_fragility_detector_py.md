# Module Analysis: `trust_system/fragility_detector.py`

## 1. Module Intent/Purpose

The primary role of the [`trust_system/fragility_detector.py`](trust_system/fragility_detector.py) module is to calculate a "fragility score" for forecasts. This score is derived from symbolic tension and overlay volatility, aiming to quantify the emotional stability of a forecast, even if the forecast itself expresses high confidence. It helps in identifying forecasts that might be unreliable due to underlying instability.

## 2. Operational Status/Completeness

The module appears to be operationally complete for its defined scope.
- It contains functions to compute the fragility score, map scores to labels, and tag forecasts with this information.
- There are no obvious placeholders (e.g., `pass` statements in critical logic) or "TODO" comments indicating unfinished work within the core functionality.
- A simple simulation function [`simulate_fragility_test()`](trust_system/fragility_detector.py:87) is included for basic testing.

## 3. Implementation Gaps / Unfinished Next Steps

- **Extensiveness:** The module is focused and does not show immediate signs of being intended to be significantly more extensive than its current state. Its scope is well-defined around fragility calculation.
- **Logical Next Steps:**
    - More sophisticated fragility metrics could be developed, perhaps incorporating historical volatility or other symbolic dimensions.
    - Integration with a real-time forecast monitoring or alerting system could be a logical follow-up.
    - The thresholds for fragility labels ([`get_fragility_label`](trust_system/fragility_detector.py:59)) could be made configurable instead of being hardcoded.
- **Deviations/Stopped Short:** There are no clear indications that development started on a planned path and then deviated or stopped short. The module delivers on its stated purpose.

## 4. Connections & Dependencies

- **Direct Project Imports:**
    - [`from symbolic_system.symbolic_utils import symbolic_tension_score`](symbolic_system/symbolic_utils.py)
    - [`from utils.log_utils import get_logger`](utils/log_utils.py)
    - [`from core.pulse_config import DEFAULT_FRAGILITY_THRESHOLD`](core/pulse_config.py)
- **External Library Dependencies:**
    - `typing.Dict` (Python standard library)
- **Interaction via Shared Data:**
    - The module primarily interacts with forecast objects, which are expected to be dictionaries.
    - It reads keys like `"overlays"`, `"symbolic_change"`, or an existing `"fragility"` score from these dictionaries.
    - It writes/updates `"fragility"` and adds `"fragility_label"` to these forecast dictionaries.
- **Input/Output Files:**
    - The module uses a logger ([`logger = get_logger(__name__)`](trust_system/fragility_detector.py:25)), which implies that log messages (e.g., debug output from [`compute_fragility`](trust_system/fragility_detector.py:53)) might be written to a log file configured elsewhere in the system. It does not directly read from or write to other data files.

## 5. Function and Class Example Usages

- **[`compute_fragility(symbolic_overlay: Dict[str, float], symbolic_change: Dict[str, float], tension_weight: float = 0.6, volatility_weight: float = 0.4, debug: bool = False) -> float`](trust_system/fragility_detector.py:28):**
    - **Purpose:** Calculates the fragility score (0.0 to 1.0).
    - **Usage:** `score = compute_fragility({"hope": 0.8, "despair": 0.1}, {"hope": -0.1, "despair": 0.05})`
- **[`get_fragility_label(score: float) -> str`](trust_system/fragility_detector.py:59):**
    - **Purpose:** Converts a numerical fragility score into a human-readable symbolic label (e.g., "🟢 Stable", "⚠️ Moderate", "🔴 Volatile").
    - **Usage:** `label = get_fragility_label(0.75)`
- **[`tag_fragility(forecasts)`](trust_system/fragility_detector.py:71):**
    - **Purpose:** Iterates through a list of forecast objects. For each forecast, it either uses an existing "fragility" score or computes one if "overlays" and "symbolic_change" data are present. It then adds/updates the "fragility" score and adds a "fragility_label" to the forecast object.
    - **Usage:**
      ```python
      forecast_list = [
          {"id": 1, "overlays": {"joy": 0.9}, "symbolic_change": {"joy": 0.05}},
          {"id": 2, "fragility": 0.2}
      ]
      tagged_forecasts = tag_fragility(forecast_list)
      # Each forecast in tagged_forecasts will now have 'fragility' and 'fragility_label'
      ```
- **[`simulate_fragility_test()`](trust_system/fragility_detector.py:87):**
    - **Purpose:** A simple inline function to demonstrate and test the fragility calculation and labeling with sample data.
    - **Usage:** Called directly when the script is run as `__main__`.

## 6. Hardcoding Issues

- **Default Weights:** The `tension_weight` (0.6) and `volatility_weight` (0.4) in [`compute_fragility`](trust_system/fragility_detector.py:31-32) are default parameters. This is acceptable as they can be overridden if needed.
- **Label Thresholds:** The thresholds (0.3, 0.6) used in [`get_fragility_label`](trust_system/fragility_detector.py:63-67) to determine labels ("🟢 Stable", "⚠️ Moderate", "🔴 Volatile") are hardcoded. These could potentially be made configurable (e.g., via `pulse_config`).
- **Volatility Normalization Divisor:** The value `5.0` in the volatility calculation (`sum(abs(v) for v in symbolic_change.values()) / 5.0`) within [`compute_fragility`](trust_system/fragility_detector.py:49) appears to be a magic number used for normalization. Its origin or rationale is not immediately clear from the code and could benefit from a comment or being defined as a constant.
- **Default Fragility Threshold:** The fragility score is capped by `DEFAULT_FRAGILITY_THRESHOLD` imported from [`core.pulse_config`](core/pulse_config.py:23). This is a good practice as the threshold is managed centrally.
- **Simulation Data:** The data within [`simulate_fragility_test`](trust_system/fragility_detector.py:91-92) is hardcoded, which is standard and expected for a self-contained test/simulation function.

## 7. Coupling Points

- **Forecast Object Structure:** The module is tightly coupled to the expected structure of forecast objects (dictionaries), requiring keys like `"overlays"`, `"symbolic_change"`, or `"fragility"`. Changes to this structure elsewhere could break this module.
- **[`symbolic_system.symbolic_utils.symbolic_tension_score`](symbolic_system/symbolic_utils.py):** The [`compute_fragility`](trust_system/fragility_detector.py:28) function directly depends on [`symbolic_tension_score`](symbolic_system/symbolic_utils.py:0) for a part of its calculation.
- **[`core.pulse_config.DEFAULT_FRAGILITY_THRESHOLD`](core/pulse_config.py):** The module relies on this centrally defined configuration value for capping the fragility score.

## 8. Existing Tests

- No dedicated test files (e.g., `test_fragility_detector.py`) were found in the `tests/trust_system/` directory or other common test locations based on the `list_files` output.
- The module includes an inline test function, [`simulate_fragility_test()`](trust_system/fragility_detector.py:87), which is executed if the script is run directly (`if __name__ == "__main__":`). This provides a basic level of testing for the core logic but does not cover edge cases or a comprehensive suite of scenarios.
- **Gaps:** Lack of a formal test suite means that regressions might not be caught easily. More comprehensive tests covering various inputs, edge cases (e.g., empty overlay/change dictionaries, extreme values), and interactions between functions would be beneficial.

## 9. Module Architecture and Flow

- **High-Level Structure:** The module consists of a set of utility functions designed to assess and label the fragility of forecasts.
- **Key Components:**
    - [`compute_fragility(...)`](trust_system/fragility_detector.py:28): Core logic for calculating the numerical fragility score. It takes symbolic overlay data and change data, calculates tension and volatility, and combines them using weights.
    - [`get_fragility_label(...)`](trust_system/fragility_detector.py:59): Translates the numerical score into a qualitative category.
    - [`tag_fragility(...)`](trust_system/fragility_detector.py:71): Orchestrates the application of fragility scoring and labeling to a collection of forecasts.
- **Primary Data/Control Flows:**
    1.  Input: A list of forecast objects (dictionaries) is typically passed to [`tag_fragility`](trust_system/fragility_detector.py:71).
    2.  For each forecast:
        a.  If "fragility" score is not present, [`compute_fragility`](trust_system/fragility_detector.py:28) is called using "overlays" and "symbolic_change" data from the forecast.
        b.  The resulting score (or pre-existing one) is then passed to [`get_fragility_label`](trust_system/fragility_detector.py:59).
        c.  The forecast dictionary is updated with the "fragility" score and "fragility_label".
    3.  Output: The list of forecasts, now annotated with fragility information.
- The [`simulate_fragility_test()`](trust_system/fragility_detector.py:87) function provides a standalone flow for testing the calculation with sample data.

## 10. Naming Conventions

- **Consistency:** Naming conventions are generally consistent and follow Python's PEP 8 guidelines for function and variable names (snake_case).
- **Clarity:**
    - Function names like [`compute_fragility`](trust_system/fragility_detector.py:28), [`get_fragility_label`](trust_system/fragility_detector.py:59), and [`tag_fragility`](trust_system/fragility_detector.py:71) are clear and descriptive of their purpose.
    - Variable names such as `symbolic_overlay`, `symbolic_change`, `tension_weight`, and `volatility_weight` are self-explanatory.
    - The use of `fc` as an abbreviation for `forecast` in the loop within [`tag_fragility`](trust_system/fragility_detector.py:76) is common and generally understandable in context.
    - Labels like "🟢 Stable", "⚠️ Moderate", "🔴 Volatile" are clear and use emojis for quick visual indication.
- **Potential AI Assumption Errors/Deviations:** No obvious errors or significant deviations from standard Python naming conventions that would suggest misinterpretation by AI or human developers were noted. The code is quite readable.