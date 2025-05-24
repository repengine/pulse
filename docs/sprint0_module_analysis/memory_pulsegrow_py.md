# Module Analysis: `memory/pulsegrow.py`

## 1. Module Intent/Purpose

The `memory/pulsegrow.py` module, named "PulseGrow — Variable Evolution Engine," is designed to introduce new candidate variables into Pulse simulations. Its primary role is to evaluate the performance of these candidate variables over time and selectively promote them to the core memory if they demonstrate an ability to enhance forecast clarity, symbolic richness, or capital foresight. Key functionalities include candidate registration, performance scoring, symbolic correlation testing, and a gated promotion process with an audit trail.

## 2. Operational Status/Completeness

The module appears largely functional for its core defined scope of registering, scoring, evaluating, and attempting to promote variables. However, several components, particularly those involving integration with a broader "PulseMemory" system, are explicitly marked as "stubs" or have placeholder comments indicating future implementation.

- **Functional:** Variable registration, basic scoring, evaluation against thresholds, and attempts to promote to `VariableRegistry`.
- **Partially Implemented/Stubbed:**
    - Logging failed candidates to a persistent memory ([`log_failed_candidate()`](memory/pulsegrow.py:108)).
    - Archiving "variable fossils" to `PulseMemory` ([`memory_feedback_loop()`](memory/pulsegrow.py:135)).
    - Reconsidering variables under different symbolic regimes ([`memory_feedback_loop()`](memory/pulsegrow.py:135)).

## 3. Implementation Gaps / Unfinished Next Steps

- **`PulseMemory` Integration:** The module frequently references a `PulseMemory` system for tasks like logging failed candidates and archiving "variable fossils" (e.g., lines 112, 145). This integration is currently stubbed and represents a significant area for future development.
- **Advanced Scoring Mechanisms:** The module docstring mentions "Performance scoring via PFPA and SUS deltas," but the actual scoring methods implemented ([`score_variable()`](memory/pulsegrow.py:46), [`score_from_forecast()`](memory/pulsegrow.py:99), [`link_symbolic_events()`](memory/pulsegrow.py:104), [`score_from_scraper()`](memory/pulsegrow.py:122)) are based on generic scores, forecast confidence/fragility, or STI/volatility. The specific PFPA (presumably Performance-Fragility-Potential-Accuracy or similar) and SUS (Symbolic Utility Score or similar) delta calculations are not explicitly detailed or implemented.
- **Symbolic Regime Reconsideration:** The concept of reconsidering a soft-retired variable under a "different symbolic regime" is mentioned as a stub ([`memory_feedback_loop()`](memory/pulsegrow.py:147)) and would require substantial logic to implement.
- **Error Handling in Promotion:** The [`promote_to_registry()`](memory/pulsegrow.py:70) method has a broad `except Exception` clause, which could be refined for more specific error handling.

## 4. Connections & Dependencies

- **Direct Project Imports:**
    - `core.variable_registry.VariableRegistry` (conditionally imported within [`promote_to_registry()`](memory/pulsegrow.py:70)) for promoting variables.
- **External Library Dependencies:**
    - `logging` (standard Python library)
    - `typing` (standard Python library: `Dict`, `List`, `Optional`)
- **Interaction with Other Modules:**
    - **`core.variable_registry`:** The primary interaction point for successfully promoted variables.
    - **`PulseMemory` (Implied):** Significant implied interaction for logging, archiving, and potentially retrieving variable performance history. This module/system is not explicitly defined within `pulsegrow.py`.
- **Input/Output Files:**
    - The module uses the `logging` module, so it will output log messages according to the configured logging setup.
    - No direct file reading or writing operations are performed by this module, aside from the implied persistence layer of `PulseMemory`.

## 5. Function and Class Example Usages

### `PulseGrow` Class

```python
# Initialization
pg = PulseGrow()

# Registering a new candidate variable
pg.register_variable(name="new_sensor_data", meta={"source": "external_api", "unit": "celsius"})

# Scoring the variable based on some evaluation
pg.score_variable(name="new_sensor_data", score=0.75)
pg.score_from_forecast(variable="new_sensor_data", confidence=0.8, fragility=0.1)
pg.link_symbolic_events(var="new_sensor_data", symbolic_event="temperature_spike_correlated_market_dip")

# Evaluating candidates and promoting them (e.g., at the end of a simulation cycle)
pg.evaluate_and_promote(threshold=0.7, min_attempts=5)

# Attempting to move promoted variables to the global registry
pg.promote_to_registry()

# Exporting audit data
audit_results = pg.export_audit()
# {'promoted': [...], 'rejected': [...], 'candidates': [...]}

# Automatic periodic evaluation (if integrated into a simulation loop)
# pg.auto_tick()

# Logging a candidate that failed for a specific reason outside normal scoring
pg.log_failed_candidate(name="experimental_feature_x", reason="Consistently negative impact")

# Tracking anomalies
pg.track_anomaly(name="new_sensor_data", sti=0.85, volatility=0.6)

# Scoring based on scraper data
pg.score_from_scraper(name="new_sensor_data", sti=0.75, volatility=0.55)

# Running memory feedback loop
pg.memory_feedback_loop(cycles=10) # Soft-retire if not promoted after 10 attempts
```

### `PulseGrowAuditRunner` Class

```python
# Assuming 'pg' is an instance of PulseGrow with registered/scored variables
audit_runner = PulseGrowAuditRunner(pulsegrow=pg)

# Review current candidate status
audit_runner.review_candidates()
# Output might be:
# Candidate: new_sensor_data | Attempts: 7 | Avg Score: 0.78 | Symbolic Links: 1

# Simulate promotion/rejection based on different thresholds
audit_runner.review_thresholds(threshold=0.8, min_attempts=3)
# Output might be:
# new_sensor_data: reject
```

## 6. Hardcoding Issues

- **Promotion Thresholds:**
    - [`evaluate_and_promote()`](memory/pulsegrow.py:56): `threshold: float = 0.7`
    - [`evaluate_and_promote()`](memory/pulsegrow.py:56): `min_attempts: int = 3`
- **Default Metadata for Promotion:**
    - [`promote_to_registry()`](memory/pulsegrow.py:76-81): Default metadata for variables promoted to `VariableRegistry` includes `{"type": "experimental", "description": "Auto-promoted from PulseGrow", "default": 0.0, "range": [0.0, 1.0]}`. These might need to be more dynamic or configurable.
- **Scoring Values:**
    - [`link_symbolic_events()`](memory/pulsegrow.py:106): Assigns a fixed score of `0.8` for any symbolic link.
    - [`score_from_scraper()`](memory/pulsegrow.py:122): Uses fixed thresholds `sti_threshold: float = 0.7`, `vol_threshold: float = 0.5`, and fixed score increments of `0.5`.
- **Memory Feedback Loop Cycles:**
    - [`memory_feedback_loop()`](memory/pulsegrow.py:135): `cycles: int = 5` for soft-retiring variables.
- **Audit Runner Default Thresholds:**
    - [`PulseGrowAuditRunner.review_thresholds()`](memory/pulsegrow.py:160): `threshold: float = 0.7`, `min_attempts: int = 3`.

## 7. Coupling Points

- **`core.variable_registry.VariableRegistry`:** The module is tightly coupled with `VariableRegistry` for the final step of making a variable official. Changes to `VariableRegistry`'s API or behavior could directly impact `PulseGrow`.
- **`PulseMemory` (Implied):** The design implies a significant coupling with a `PulseMemory` system for persistence and advanced variable lifecycle management. The absence or different implementation of `PulseMemory` would require changes in `PulseGrow`.
- **Scoring Logic:** The methods for scoring variables ([`score_from_forecast()`](memory/pulsegrow.py:99), [`link_symbolic_events()`](memory/pulsegrow.py:104), [`score_from_scraper()`](memory/pulsegrow.py:122)) imply coupling with external systems or logic that provide inputs like `confidence`, `fragility`, `sti`, and `volatility`.

## 8. Existing Tests

Based on the file listing of the `tests/` directory, there does not appear to be a specific test file for `memory/pulsegrow.py` (e.g., `tests/memory/test_pulsegrow.py` or `tests/test_pulsegrow.py`). This indicates a potential gap in test coverage for this module.

## 9. Module Architecture and Flow

The module is structured around two classes: `PulseGrow` and `PulseGrowAuditRunner`.

**`PulseGrow` Class:**
- **State:** Manages dictionaries and lists for `candidates`, `promoted`, and `rejected` variables. Each candidate stores metadata, scores, symbolic links, and attempt counts.
- **Registration:** New variables are added via [`register_variable()`](memory/pulsegrow.py:30).
- **Scoring:** Variables accumulate scores through various methods:
    - Direct scoring: [`score_variable()`](memory/pulsegrow.py:46)
    - Forecast-based: [`score_from_forecast()`](memory/pulsegrow.py:99)
    - Symbolic linkage: [`link_symbolic_events()`](memory/pulsegrow.py:104)
    - Scraper-based (STI/volatility): [`score_from_scraper()`](memory/pulsegrow.py:122)
- **Evaluation & Promotion:**
    - [`evaluate_and_promote()`](memory/pulsegrow.py:56): Periodically checks candidates against score thresholds and minimum attempts. Moves them to `promoted` or `rejected` lists.
    - [`promote_to_registry()`](memory/pulsegrow.py:70): Attempts to register `promoted` variables with `core.variable_registry.VariableRegistry`.
- **Lifecycle Management:**
    - [`auto_tick()`](memory/pulsegrow.py:94): Combines evaluation and registry promotion for periodic execution.
    - [`memory_feedback_loop()`](memory/pulsegrow.py:135): Implements a "soft retirement" policy for variables that fail to get promoted after a certain number of attempts, with stubs for archiving.
- **Anomaly Tracking:** [`track_anomaly()`](memory/pulsegrow.py:114) flags variables based on STI/volatility.
- **Auditing:** [`export_audit()`](memory/pulsegrow.py:86) provides a summary of promotion results.

**`PulseGrowAuditRunner` Class:**
- This class acts as a utility to review the state of a `PulseGrow` instance.
- [`review_candidates()`](memory/pulsegrow.py:154): Prints a summary of all candidates and their current scores/status.
- [`review_thresholds()`](memory/pulsegrow.py:160): Simulates and shows which candidates would be promoted or rejected given specific threshold values, allowing for "what-if" analysis of promotion criteria.

**Data Flow:**
1. External systems or processes generate new potential variables.
2. These are registered with `PulseGrow` via [`register_variable()`](memory/pulsegrow.py:30).
3. Over time, as these variables are used in simulations or analyzed, scores are added via methods like [`score_variable()`](memory/pulsegrow.py:46), [`score_from_forecast()`](memory/pulsegrow.py:99), etc.
4. Periodically (e.g., via [`auto_tick()`](memory/pulsegrow.py:94) or manual call to [`evaluate_and_promote()`](memory/pulsegrow.py:56)), candidates are assessed.
5. Successful candidates are moved to the `promoted` list and then attempted to be registered in the global `VariableRegistry` via [`promote_to_registry()`](memory/pulsegrow.py:70).
6. Unsuccessful or consistently underperforming variables may be "soft-retired" by the [`memory_feedback_loop()`](memory/pulsegrow.py:135).
7. Audit data can be exported or reviewed using [`export_audit()`](memory/pulsegrow.py:86) or `PulseGrowAuditRunner`.

## 10. Naming Conventions

- **General:** The module generally adheres to PEP 8 naming conventions for classes (`PulseGrow`, `PulseGrowAuditRunner`), methods (e.g., [`register_variable`](memory/pulsegrow.py:30), [`evaluate_and_promote`](memory/pulsegrow.py:56)), and variables (e.g., `avg_score`, `min_attempts`).
- **Clarity:** Names are mostly descriptive and indicate their purpose.
- **Compatibility:** The [`register_variable()`](memory/pulsegrow.py:30) method accepts both `meta` and `metadata` as parameter names for compatibility, preferring `meta`. This is a practical approach.
- **Abbreviations/Acronyms:**
    - `sti`: Used in [`track_anomaly()`](memory/pulsegrow.py:114) and [`score_from_scraper()`](memory/pulsegrow.py:122). While not explicitly defined in this file, context suggests it might relate to "Symbolic Trigger Intensity" or a similar project-specific term. Its meaning should ideally be documented or made clearer.
    - `PFPA` and `SUS`: Mentioned in the module docstring but not used in the code, their full forms are not provided.
- **Consistency:**
    - `name` is consistently used for variable identifiers.
    - `score`/`scores` are used for performance metrics.
- **Potential AI Assumption Errors:** The code seems human-written and conventional. The "Author: Pulse v0.304" in the docstring might be a versioning tag rather than an AI author attribution. No obvious AI-like naming errors are apparent.