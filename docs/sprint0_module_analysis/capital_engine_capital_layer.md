# Module Analysis: capital_engine/capital_layer.py

## 1. Module Path

[`capital_engine/capital_layer.py`](capital_engine/capital_layer.py:1)

## 2. Purpose & Functionality

The `capital_layer.py` module serves as a **Unified Capital Simulation Layer** within the Pulse application. Its primary purpose is to translate symbolic system states (represented by "overlays" like hope, despair, trust) into simulated capital adjustments for a predefined set of financial assets.

Key functionalities include:

*   **Symbolic-Driven Asset Forks:** Adjusting capital allocations for specific assets (currently NVDA, MSFT, IBIT, SPY) based on formulas that combine various symbolic overlay values and predefined thresholds/weights.
*   **Portfolio State Summarization:** Providing functions to calculate and report on the current portfolio's capital exposure, including total exposure and percentage allocation per asset.
*   **Short-Term Symbolic Foresight:** Simulating the impact of symbolic changes on capital over a short duration (1-7 days), providing a forecast that includes capital deltas, symbolic changes, and portfolio alignment tags.
*   **Role:** Within the `capital_engine/` directory, this module is central to simulating how symbolic interpretations of events or states affect capital. In the broader Pulse application, it acts as a bridge between the abstract symbolic reasoning system and a more concrete (though still simulated) financial portfolio management layer.

## 3. Key Components / Classes / Functions

The module is composed of several functions:

*   **Symbolic-to-Capital Fork Logic:**
    *   [`simulate_nvda_fork(state: WorldState) -> None`](capital_engine/capital_layer.py:23): Simulates capital adjustment for NVDA based on symbolic overlays.
    *   [`simulate_msft_fork(state: WorldState) -> None`](capital_engine/capital_layer.py:32): Simulates capital adjustment for MSFT.
    *   [`simulate_ibit_fork(state: WorldState) -> None`](capital_engine/capital_layer.py:40): Simulates capital adjustment for IBIT.
    *   [`simulate_spy_fork(state: WorldState) -> None`](capital_engine/capital_layer.py:48): Simulates capital adjustment for SPY.
    *   [`run_capital_forks(state: WorldState, assets: Optional[List[str]] = None) -> None`](capital_engine/capital_layer.py:57): Orchestrates the execution of individual asset fork simulations.

*   **Portfolio State Summary:**
    *   [`summarize_exposure(state: WorldState) -> Dict[str, float]`](capital_engine/capital_layer.py:68): Returns a dictionary of current capital exposure per asset.
    *   [`total_exposure(state: WorldState) -> float`](capital_engine/capital_layer.py:74): Calculates the total capital exposure across tracked assets.
    *   [`exposure_percentages(state: WorldState) -> Dict[str, float]`](capital_engine/capital_layer.py:81): Calculates the percentage exposure for each asset relative to the total.
    *   [`portfolio_alignment_tags(state: WorldState) -> Dict[str, str]`](capital_engine/capital_layer.py:97): Generates tags ("growth-aligned", "defensive", "neutral") based on trust and fatigue overlays.

*   **Short-Term Symbolic Forecast Layer:**
    *   [`run_shortview_forecast(state: WorldState, asset_subset: Optional[List[str]] = None, duration_days: int = 2) -> Dict[str, Any]`](capital_engine/capital_layer.py:111): Orchestrates a short-term forecast by running capital forks, snapshotting state changes, and calculating symbolic fragility, capital deltas, and symbolic changes.

## 4. Dependencies

*   **Internal Pulse Modules:**
    *   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py)
    *   [`simulation_engine.state_mutation.adjust_capital`](simulation_engine/state_mutation.py)
    *   [`core.variable_accessor.get_overlay`](core/variable_accessor.py)
    *   [`core.pulse_config`](core/pulse_config.py) (constants: `CONFIDENCE_THRESHOLD`, `DEFAULT_FRAGILITY_THRESHOLD`, `TRUST_WEIGHT`, `DESPAIR_WEIGHT`)
    *   [`symbolic_system.symbolic_utils.symbolic_fragility_index`](symbolic_system/symbolic_utils.py)
*   **External Libraries:**
    *   `typing` (Dict, Optional, List, Any)

## 5. SPARC Analysis

*   **Specification:**
    *   The module's purpose is generally clear from its docstring and functional breakdown.
    *   Requirements for capital management are implicitly defined by the hardcoded formulas within the `simulate_<asset>_fork` functions. The rationale and origin of these specific formulas are not documented within this module, making their specification opaque.

*   **Architecture & Modularity:**
    *   The module exhibits good modularity with distinct sections for fork logic, summarization, and forecasting.
    *   Functions are mostly focused and have clear responsibilities.
    *   The use of the `WorldState` object as a central data carrier promotes a degree of separation.

*   **Refinement - Testability:**
    *   No dedicated unit tests are present in the file.
    *   Functions are generally testable due to clear inputs (`WorldState`) and outputs, provided `WorldState` and its dependencies can be mocked.
    *   A single `assert` statement in [`run_shortview_forecast`](capital_engine/capital_layer.py:189) provides a very basic runtime check but is not a substitute for a proper testing strategy.

*   **Refinement - Maintainability:**
    *   Code is generally readable with descriptive function names and type hints.
    *   The main forecasting function has a good docstring, but individual fork simulation functions and summarization functions lack detailed explanations, especially regarding the logic of their calculations.
    *   Constants are defined at the module level, which is good practice.
    *   Error handling is present but sometimes uses broad exceptions (e.g., `except AttributeError`, `except Exception`).

*   **Refinement - Security:**
    *   The module operates on simulated data. No direct external interactions (APIs, user input handling for sensitive data) are apparent, minimizing immediate security risks.
    *   If `WorldState` were to handle real financial data or execute real transactions, a thorough security review would be critical.

*   **Refinement - No Hardcoding:**
    *   **Significant Hardcoding:**
        *   **Asset Symbols:** "nvda", "msft", "ibit", "spy" are hardcoded throughout the module.
        *   **Simulation Parameters:** Numeric multipliers (e.g., `1000`, `800`, `1200`, `900`) in fork functions are hardcoded.
        *   **Symbolic Coefficients:** Weights for symbolic overlays in fork formulas (e.g., `r * 0.3`, `h * 0.4`) are hardcoded.
        *   **Thresholds:** `TRUST_GROWTH_THRESHOLD` and `FATIGUE_DEFENSIVE_THRESHOLD` are constants but their values are fixed in the code.
        *   Forecast duration limits (`MIN_DURATION`, `MAX_DURATION`) are hardcoded.
    *   This hardcoding severely limits flexibility, extensibility, and makes adjustments difficult without code modification.

## 6. Identified Gaps & Areas for Improvement

*   **Configuration Management:**
    *   **Gap:** Extensive hardcoding of asset names, simulation multipliers, and symbolic coefficients.
    *   **Improvement:** Externalize these parameters into configuration files (e.g., YAML, JSON) to allow easier modification and extension without code changes.
*   **Documentation:**
    *   **Gap:** Lack of detailed docstrings for many functions, especially the `simulate_<asset>_fork` functions, which do not explain the rationale behind their specific formulas.
    *   **Improvement:** Add comprehensive docstrings explaining the logic, parameters, and assumptions of each function.
*   **Testability:**
    *   **Gap:** Absence of a dedicated test suite.
    *   **Improvement:** Develop unit tests for all functions, focusing on mocking `WorldState` and verifying capital adjustments and forecast outputs.
*   **Extensibility:**
    *   **Gap:** Adding new assets requires manual code additions for new `simulate_..._fork` functions and updates to [`run_capital_forks`](capital_engine/capital_layer.py:57).
    *   **Improvement:** Design a more data-driven or plugin-based architecture for defining asset-specific simulation logic.
*   **Symbolic Logic Transparency:**
    *   **Gap:** The derivation and meaning of the specific formulas used in the asset fork simulations are not clear.
    *   **Improvement:** Document the source or reasoning for these formulas, or link to external documentation/specification if it exists.
*   **Feature Completeness:**
    *   **Gap:** The `confidence` score in the [`run_shortview_forecast`](capital_engine/capital_layer.py:111) output is a placeholder (`None`).
    *   **Improvement:** Implement the logic for calculating forecast confidence.
*   **Code Hygiene:**
    *   **Gap:** The import `MODULES_ENABLED` from [`core.pulse_config`](core/pulse_config.py:15) is not used.
    *   **Improvement:** Remove unused imports.
*   **Error Handling:**
    *   **Gap:** Some exception handling is too broad.
    *   **Improvement:** Refine error handling to catch more specific exceptions where appropriate and provide more context.

## 7. Overall Assessment & Next Steps

*   **Overall Assessment:**
    The [`capital_layer.py`](capital_engine/capital_layer.py:1) module provides a functional, albeit rigid, implementation for simulating capital adjustments based on symbolic states and for generating basic short-term forecasts. It is moderately well-structured but is significantly hampered by hardcoding, which impacts its maintainability, extensibility, and overall quality. The lack of thorough documentation for its core logic and the absence of tests are key weaknesses.

*   **Quality:** Moderate. Readable code but needs improvement in configurability, documentation, and testing.
*   **Completeness:** Partially complete. It fulfills its basic stated functions for the hardcoded assets but lacks flexibility and has placeholder features (e.g., confidence score).

*   **Recommended Next Steps:**
    1.  **Refactor for Configuration:** Prioritize moving all hardcoded asset names, multipliers, and symbolic coefficients to external configuration files.
    2.  **Enhance Documentation:** Add detailed docstrings to all functions, particularly explaining the rationale behind the symbolic fork logic.
    3.  **Develop Unit Tests:** Create a comprehensive suite of unit tests to ensure reliability and facilitate future refactoring.
    4.  **Improve Extensibility:** Investigate and implement a more flexible mechanism for defining and managing asset-specific simulation rules.
    5.  **Implement Confidence Score:** Complete the forecast confidence calculation.
    6.  **Code Cleanup:** Remove unused imports and refine error handling.