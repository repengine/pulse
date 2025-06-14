# Module Analysis: forecast_engine/forecast_scoring.py

## 1. Purpose

The [`forecast_engine/forecast_scoring.py`](../../forecast_engine/forecast_scoring.py:1) module is responsible for evaluating and assigning trust-related metrics to individual forecasts generated by the simulation engine. It assesses forecasts based on criteria such as the richness of rule activations, symbolic coherence (dominant symbolic tags), and an inferred measure of fragility. The output scores (`confidence`, `fragility`, `symbolic_driver`) are intended to provide a quantitative measure of a forecast's reliability.

## 2. Key Functionalities

*   **Forecast Scoring (`score_forecast`)**:
    *   Takes the final [`WorldState`](../../simulation_engine/worldstate.py:1) of a simulation and a `rule_log` (a list of dictionaries representing activated rules) as input.
    *   Analyzes the `rule_log` to count occurrences of `symbolic_tags` associated with activated rules.
    *   Determines the `symbolic_driver` as the most frequent symbolic tag.
    *   Calculates a `confidence` score, which increases with the diversity (number of unique types) of symbolic tags activated. The score is capped at 0.95.
    *   Calculates a `fragility` score, which decreases with the diversity of symbolic tags. This implies that forecasts relying on a narrow set of symbolic drivers are considered more fragile. The score is bounded between 0.0 and 1.0.
    *   If the `rule_log` is empty (no rules activated), it returns default low confidence (0.1) and high fragility (0.9) scores.
    *   Logs the scoring event, including the calculated metrics and a timestamp, using [`log_learning_event`](../../core/pulse_learning_log.py:15) from [`core.pulse_learning_log`](../../core/pulse_learning_log.py:1).

## 3. Dependencies

### External Libraries:
*   [`datetime`](https://docs.python.org/3/library/datetime.html) (from `datetime`): Used to timestamp the learning event log.

### Internal Pulse Modules:
*   [`engine.worldstate.WorldState`](../../simulation_engine/worldstate.py:1): The `state` argument is typed as `WorldState`, although it's not directly used in the current logic of [`score_forecast`](../../forecast_engine/forecast_scoring.py:17). This suggests a potential for future enhancements where the world state itself might influence scoring.
*   [`core.pulse_learning_log.log_learning_event`](../../core/pulse_learning_log.py:15): Used to log the outcome of the forecast scoring process.

## 4. Adherence to SPARC Principles

*   **Simplicity**: The scoring logic is relatively simple and based on a few heuristics related to symbolic tag diversity. The code is concise and easy to follow.
*   **Iterate**: The module contributes to an iterative learning process by providing scores that can be used to evaluate and refine the forecasting models or rules. The logging of scoring events supports this.
*   **Focus**: The module is sharply focused on its task of scoring forecasts based on the provided inputs.
*   **Quality**:
    *   The module includes type hints and a docstring for the main function.
    *   The use of [`log_learning_event`](../../core/pulse_learning_log.py:15) indicates integration with a structured logging system for learning processes.
    *   The scoring heuristics (e.g., `0.5 + (0.05 * diversity_factor)` for confidence) are clear but might be somewhat arbitrary without further context or empirical validation. The comments "Confidence: more diverse symbolic signals = more believable" and "Fragility: based on symbolic over-weighting" provide some rationale.
    *   The `WorldState` argument is currently unused, which could be seen as a minor quality issue (dead parameter) or an indicator of planned future enhancements.
*   **Collaboration**: The module collaborates by consuming output from the rule engine (`rule_log`) and providing scores that other parts of the system (e.g., forecast selection, model tuning) can use.

## 5. Overall Assessment

*   **Completeness**:
    *   The module is complete for its currently defined scoring logic. It successfully calculates confidence, fragility, and identifies a symbolic driver based on rule activation patterns.
    *   The criteria mentioned in the module docstring ("Rule activation richness", "Symbolic coherence (tag overlap)", "Variable sensitivity (volatility)", "Potential for divergence (fragility)") are partially addressed. "Rule activation richness" and "Symbolic coherence" are captured through symbolic tag diversity and the dominant driver. "Fragility" is explicitly calculated. However, "Variable sensitivity (volatility)" and a more direct measure of "Potential for divergence" are not explicitly incorporated into the scoring logic using the `WorldState` yet.
*   **Clarity**:
    *   The code is clear and the logic for calculating scores is straightforward.
    *   Variable names are descriptive.
    *   The rationale behind the scoring (more diversity = higher confidence, lower fragility) is understandable.
*   **Quality**:
    *   The code is of good quality for its current scope.
    *   The scoring heuristics are simple; their effectiveness would depend on empirical validation within the broader Pulse system.
    *   The unused `WorldState` parameter in [`score_forecast`](../../forecast_engine/forecast_scoring.py:17) should either be utilized in future enhancements (e.g., to assess variable sensitivity) or removed if not planned for use.
    *   Lack of dedicated unit tests for this module is a gap. Testing different `rule_log` scenarios would be beneficial.

**Recommendations**:
*   Consider incorporating the `WorldState` data to assess "variable sensitivity" or other factors that could enhance the scoring, as hinted by the module's docstring and the unused parameter.
*   Empirically validate and potentially refine the scoring heuristics (e.g., the coefficients `0.05` and `0.03`) to ensure they meaningfully reflect forecast quality.
*   Develop unit tests for the [`score_forecast`](../../forecast_engine/forecast_scoring.py:17) function to cover various `rule_log` inputs, including empty logs, logs with single tags, and logs with multiple diverse tags.
*   Clarify if "symbolic over-weighting" as a basis for fragility refers purely to low diversity or if other aspects of rule weights/importance are intended to be included in the future.