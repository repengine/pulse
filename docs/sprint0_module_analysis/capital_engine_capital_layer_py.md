# Analysis of capital_engine/capital_layer.py

## Module Intent/Purpose
This module, the "Unified Capital Simulation Layer," simulates capital allocation changes based on symbolic overlays, summarizes portfolio states, and generates short-term capital forecasts. It models how overlays like "hope" or "despair" influence asset exposure for specific assets (e.g., "nvda", "spy") by adjusting capital in the `WorldState`.

## Operational Status/Completeness
Largely operational. Functions for simulating capital forks, portfolio summarization, and short-term forecasting are implemented. Integrates with `WorldState` and `core.pulse_config`. Basic error handling is present.
- Placeholder: The `\"confidence\"` field in `run_shortview_forecast` output is `None`.

## Implementation Gaps / Unfinished Next Steps
- **Confidence Calculation:** Needs implementation for the forecast's `confidence` metric.
- **Dynamic Asset Fork Logic:** Asset-specific fork logic (for "nvda", "msft", etc.) with hardcoded multipliers and overlay combinations should be made data-driven or configurable.
- **Extensibility of Fork Logic:** Adding new assets or changing symbolic logic requires code modification.
- **Sophistication of Symbolic Interaction:** Current symbolic-to-capital logic is simple; more complex models could be explored.
- **`WorldState.snapshot()` Robustness:** Error handling around `state.snapshot()` suggests potential for improvement.
- **Parameterization:** Some thresholds/weights are local; centralizing them in config would be better.
- **Testing:** Comprehensive unit tests are needed.

## Connections & Dependencies
- **Direct Project Module Imports:**
    - `engine.worldstate.WorldState`
    - `engine.state_mutation.adjust_capital`
    - `core.variable_accessor.get_overlay`
    - `core.pulse_config` (for constants like `CONFIDENCE_THRESHOLD`)
    - `symbolic_system.symbolic_utils.symbolic_fragility_index`
- **External Library Dependencies:** `typing`.
- **Interaction:** Deeply interacts with `WorldState`. Relies on `core.pulse_config` and utilities from `core.variable_accessor`, `symbolic_system.symbolic_utils`.
- **Input/Output Files:** None directly.

## Function and Class Example Usages
- **`simulate_nvda_fork(state: WorldState)`**: Calculates capital adjustment for "nvda" based on overlays.
- **`run_capital_forks(state: WorldState, ...)`**: Orchestrates individual asset fork simulations.
- **`summarize_exposure(state: WorldState)`**: Returns current capital exposures.
- **`portfolio_alignment_tags(state: WorldState)`**: Determines portfolio bias based on overlays.
- **`run_shortview_forecast(state: WorldState, ...)`**: Simulates capital changes and symbolic metrics for a forecast.

## Hardcoding Issues
- Asset names ("nvda", "msft", etc.) and symbolic overlay names are hardcoded in fork logic and summarization.
- Multipliers and coefficients in delta calculations for capital adjustments are hardcoded.
- Thresholds for alignment tags (`TRUST_GROWTH_THRESHOLD`, `FATIGUE_DEFENSIVE_THRESHOLD`) are local constants.
- Forecast duration limits (`MIN_DURATION`, `MAX_DURATION`).
- Log message prefixes.

## Coupling Points
- Tightly coupled to `WorldState` object structure and methods.
- Relies on specific constants in `core.pulse_config`.
- Logic tied to particular asset and overlay identifiers.

## Existing Tests
- No dedicated test file apparent. Minimal runtime assertion in `run_shortview_forecast`.

## Module Architecture and Flow
1.  Defines parameters, imports components.
2.  **Symbolic-to-Capital Fork Logic:** Asset-specific functions retrieve overlays, calculate delta, adjust capital in `WorldState`, log event. `run_capital_forks` dispatches these.
3.  **Portfolio State Summary Logic:** Functions to get exposures, total exposure, percentages, and alignment tags from `WorldState`.
4.  **Short-Term Forecast Layer (`run_shortview_forecast`):** Takes `WorldState` snapshot, runs capital forks, takes end snapshot, calculates overlay/capital deltas, fragility, alignment, constructs and logs forecast dictionary.

## Naming Conventions
- Generally follows PEP 8. Descriptive names. Single-letter variables in fork functions are locally clear.