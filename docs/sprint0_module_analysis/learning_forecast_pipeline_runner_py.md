# Analysis Report for `learning/forecast_pipeline_runner.py`

## Module Intent/Purpose
The primary role of [`learning/forecast_pipeline_runner.py`](learning/forecast_pipeline_runner.py) is to orchestrate and execute the comprehensive Pulse forecast processing pipeline. This involves taking raw forecast objects and subjecting them to a series of analytical, filtering, and enrichment steps, ultimately producing processed forecasts, digests, and storing relevant information in memory. The pipeline aims to enhance the quality, reliability, and utility of forecasts generated by the Pulse system.

## Operational Status/Completeness
The module appears to be largely complete and operational for its defined scope. It includes a sequence of processing steps, error handling for each major step, and logging throughout the pipeline.
*   There are comments like `# OPTIONAL: Drop rejected forecasts from pipeline` ([`learning/forecast_pipeline_runner.py:92`](learning/forecast_pipeline_runner.py:92)) which suggest some flexibility or alternative paths.
*   Placeholders for state information exist, e.g., `# Replace with state.to_dict() if state is available` ([`learning/forecast_pipeline_runner.py:154`](learning/forecast_pipeline_runner.py:154)) and commented-out Capital Layer integration dependent on `state` ([`learning/forecast_pipeline_runner.py:302-303`](learning/forecast_pipeline_runner.py:302-303)).
*   The author is listed as "Pulse v0.23" ([`learning/forecast_pipeline_runner.py:14`](learning/forecast_pipeline_runner.py:14)), indicating it's part of a versioned system.

## Implementation Gaps / Unfinished Next Steps
*   **State Integration:** The most prominent gap is the full integration of a `WorldState` object. Several comments indicate that parts of the pipeline (e.g., logging input state for trace memory and variable performance tracking, Capital Layer integration) are designed to use state information but currently use placeholders or are commented out.
    *   `# Replace with state.to_dict() if state is available` ([`learning/forecast_pipeline_runner.py:154`](learning/forecast_pipeline_runner.py:154))
    *   `input_state = f.get("input_state", {}) # Replace with actual sim state if available` ([`learning/forecast_pipeline_runner.py:157`](learning/forecast_pipeline_runner.py:157))
    *   `# If you have a WorldState object, pass it here. Otherwise, adapt as needed.` ([`learning/forecast_pipeline_runner.py:301-303`](learning/forecast_pipeline_runner.py:301-303))
*   **Symbolic Overlays Error Handling:** The import for `compute_arc_label` ([`learning/forecast_pipeline_runner.py:129`](learning/forecast_pipeline_runner.py:129)) is wrapped in a `try-except ImportError`, suggesting it might be an optional or separately installed component. If it's core, this might indicate a potential setup or dependency issue to be resolved.
*   **Variable Recommender Path:** The variable recommender is invoked via `subprocess.run` ([`learning/forecast_pipeline_runner.py:280-286`](learning/forecast_pipeline_runner.py:280-286)) calling `irldata.variable_recommender`. This external process call might be a point of fragility or could potentially be integrated more directly as a Python module call if `irldata` is part of the same broader project.
*   **Epistemic Mirror Data Sources:** The Epistemic Mirror integration relies on specific keys in the forecast dictionary like `"gpt_output"`, `"gpt_narrative"`, `"gpt_forecast"`, `"pulse_domains"`, `"pulse_rules"`, `"pulse_data"`, and `"gpt_data"` ([`learning/forecast_pipeline_runner.py:165-187`](learning/forecast_pipeline_runner.py:165-187)). The completeness of this integration depends on the consistent availability and structure of these data points in the input forecasts.

## Connections & Dependencies
### Direct imports from other project modules:
*   [`core.pulse_config`](core/pulse_config.py): `USE_SYMBOLIC_OVERLAYS`
*   [`forecast_output.forecast_compressor`](forecast_output/forecast_compressor.py): [`compress_forecasts()`](forecast_output/forecast_compressor.py)
*   [`intelligence.forecast_schema`](intelligence/forecast_schema.py): [`ForecastSchema`](intelligence/forecast_schema.py)
*   [`forecast_output.forecast_summary_synthesizer`](forecast_output/forecast_summary_synthesizer.py): [`summarize_forecasts()`](forecast_output/forecast_summary_synthesizer.py)
*   [`forecast_output.strategos_digest_builder`](forecast_output/strategos_digest_builder.py): [`build_digest()`](forecast_output/strategos_digest_builder.py)
*   [`trust_system.trust_engine`](trust_system/trust_engine.py): [`TrustEngine`](trust_system/trust_engine.py)
*   [`trust_system.fragility_detector`](trust_system/fragility_detector.py): [`tag_fragility()`](trust_system/fragility_detector.py)
*   [`analytics.trace_audit_engine`](memory/trace_audit_engine.py): [`assign_trace_metadata()`](memory/trace_audit_engine.py), [`register_trace_to_memory()`](memory/trace_audit_engine.py)
*   [`analytics.forecast_memory`](memory/forecast_memory.py): [`ForecastMemory`](memory/forecast_memory.py)
*   [`utils.log_utils`](utils/log_utils.py): [`log_info()`](utils/log_utils.py)
*   [`forecast_output.forecast_prioritization_engine`](forecast_output/forecast_prioritization_engine.py): [`select_top_forecasts()`](forecast_output/forecast_prioritization_engine.py)
*   [`analytics.forecast_memory_promoter`](memory/forecast_memory_promoter.py): [`select_promotable_forecasts()`](memory/forecast_memory_promoter.py), [`export_promoted()`](memory/forecast_memory_promoter.py)
*   [`capital_engine.capital_layer`](capital_engine/capital_layer.py): [`run_capital_forks()`](capital_engine/capital_layer.py), [`summarize_exposure()`](capital_engine/capital_layer.py), [`portfolio_alignment_tags()`](capital_engine/capital_layer.py) (Note: `run_capital_forks` is imported but not directly used in `run_forecast_pipeline`)
*   [`forecast_output.forecast_confidence_gate`](forecast_output/forecast_confidence_gate.py): [`filter_by_confidence()`](forecast_output/forecast_confidence_gate.py)
*   [`analytics.trace_memory`](memory/trace_memory.py): [`TraceMemory`](memory/trace_memory.py)
*   [`analytics.variable_performance_tracker`](memory/variable_performance_tracker.py): [`VariablePerformanceTracker`](memory/variable_performance_tracker.py)
*   [`forecast_output.forecast_contradiction_detector`](forecast_output/forecast_contradiction_detector.py): [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py)
*   [`core.pulse_learning_log`](core/pulse_learning_log.py): [`log_learning_event()`](core/pulse_learning_log.py)
*   [`GPT.gpt_causal_translator`](GPT/gpt_causal_translator.py): [`extract_rules_from_gpt_output()`](GPT/gpt_causal_translator.py), [`label_symbolic_arcs()`](GPT/gpt_causal_translator.py), [`identify_missing_domains()`](GPT/gpt_causal_translator.py)
*   [`GPT.gpt_rule_fingerprint_extractor`](GPT/gpt_rule_fingerprint_extractor.py): [`extract_fingerprint_from_gpt_rationale()`](GPT/gpt_rule_fingerprint_extractor.py), [`match_fingerprint_to_pulse_rules()`](GPT/gpt_rule_fingerprint_extractor.py), [`archive_foreign_fingerprint()`](GPT/gpt_rule_fingerprint_extractor.py)
*   [`GPT.gpt_symbolic_convergence_loss`](GPT/gpt_symbolic_convergence_loss.py): [`compute_symbolic_convergence_loss()`](GPT/gpt_symbolic_convergence_loss.py)
*   [`GPT.gpt_forecast_divergence_logger`](GPT/gpt_forecast_divergence_logger.py): [`tag_divergence_type()`](GPT/gpt_forecast_divergence_logger.py), [`log_forecast_divergence()`](GPT/gpt_forecast_divergence_logger.py)
*   [`symbolic_system.pulse_symbolic_arc_tracker`](symbolic_system/pulse_symbolic_arc_tracker.py): [`compute_arc_label()`](symbolic_system/pulse_symbolic_arc_tracker.py) (conditionally imported)

### External library dependencies:
*   `typing` (standard library)
*   `pydantic`: [`ValidationError`](https://docs.pydantic.dev/latest/api/errors/#pydantic.errors.ValidationError) (imported on line [`learning/forecast_pipeline_runner.py:21`](learning/forecast_pipeline_runner.py:21))
*   `os` (standard library)
*   `json` (standard library)
*   `subprocess` (standard library, used for [`irldata.variable_recommender`](learning/forecast_pipeline_runner.py:281))

### Interaction with other modules via shared data:
*   **Forecast Objects (Dicts):** The primary data structure passed through the pipeline. Modules modify these dictionaries by adding keys (e.g., `confidence`, `fragility_tags`, `arc_label`, `trace_id`, `gpt_extracted_rules`, etc.).
*   **ForecastMemory:** Stores compressed forecasts.
*   **TraceMemory:** Logs trace entries.
*   **VariablePerformanceTracker:** Logs variable contributions and exports scores.
*   **Pulse Learning Log:** Logs events like forecast contradictions.
*   **GPT Fingerprint Archive:** [`archive_foreign_fingerprint()`](GPT/gpt_rule_fingerprint_extractor.py) likely writes to a shared resource.

### Input/output files:
*   **Input:** Expects a list of forecast dictionaries.
*   **Output (Logs/Data Files):**
    *   `logs/strategic_batch_output.jsonl`: Stores top N selected forecasts ([`learning/forecast_pipeline_runner.py:251-255`](learning/forecast_pipeline_runner.py:251-255)).
    *   `logs/recommended_vars.json`: Output by the external `irldata.variable_recommender` script ([`learning/forecast_pipeline_runner.py:284`](learning/forecast_pipeline_runner.py:284)).
    *   General logging via [`log_info()`](utils/log_utils.py) (destination depends on logging configuration).
    *   [`VariablePerformanceTracker.export_variable_scores()`](memory/variable_performance_tracker.py) likely writes variable scores to a file (path determined within that module).
    *   [`ForecastMemory.store()`](memory/forecast_memory.py) and [`export_promoted()`](memory/forecast_memory_promoter.py) write to memory storage (details depend on `ForecastMemory` implementation).
    *   [`register_trace_to_memory()`](memory/trace_audit_engine.py) writes to trace memory.

## Function and Class Example Usages
*   **[`run_forecast_pipeline(forecasts: List[Dict[str, Any]], ... ) -> Dict[str, Any]`](learning/forecast_pipeline_runner.py:54-71):**
    *   This is the main function of the module.
    *   **Usage:** It takes a list of raw forecast dictionaries. Each dictionary is expected to have certain keys that are processed and augmented throughout the pipeline (e.g., `'confidence'`, `'symbolic_tag'`, and potentially GPT-related fields like `'gpt_output'`, `'pulse_data'`, `'gpt_data'`).
    *   It returns a dictionary summarizing the pipeline execution, including status, counts of processed forecasts, the generated digest, and top forecasts.
    *   Example from `_test_pipeline()`:
        ```python
        sample = [
            {"confidence": 0.71, "symbolic_tag": "hope", "drivers": ["AI rally"]},
            {"confidence": 0.43, "symbolic_tag": "fatigue", "drivers": ["media overload"]}
        ]
        result = run_forecast_pipeline(sample)
        ```

*   **[`_test_pipeline()`](learning/forecast_pipeline_runner.py:307-315):**
    *   A private utility function used for basic testing of the pipeline logic from the command line.
    *   **Usage:** Called when the script is run directly (`if __name__ == "__main__":`). It creates a sample list of forecasts and passes them to `run_forecast_pipeline`, then prints the JSON-formatted result.

## Hardcoding Issues
*   **Log file paths:**
    *   `"logs/strategic_batch_output.jsonl"` ([`learning/forecast_pipeline_runner.py:251`](learning/forecast_pipeline_runner.py:251))
    *   `"logs/recommended_vars.json"` (output path for `irldata.variable_recommender` subprocess call, [`learning/forecast_pipeline_runner.py:284`](learning/forecast_pipeline_runner.py:284))
    These should ideally be configurable, perhaps via `pulse_config` or environment variables.
*   **Top N forecasts:** `top_n=5` for [`select_top_forecasts()`](forecast_output/forecast_prioritization_engine.py) ([`learning/forecast_pipeline_runner.py:250`](learning/forecast_pipeline_runner.py:250)).
*   **Variable Recommender parameters:**
    *   `"--top_n", "10"` ([`learning/forecast_pipeline_runner.py:282`](learning/forecast_pipeline_runner.py:282))
    *   `"--min_count", "5"` ([`learning/forecast_pipeline_runner.py:283`](learning/forecast_pipeline_runner.py:283))
*   **Default "arc_unknown":** Used if `compute_arc_label` fails or is not available ([`learning/forecast_pipeline_runner.py:140, 142`](learning/forecast_pipeline_runner.py:140)).
*   **Default "unknown" trace_id:** Used if `trace_id` is not found in forecast for `trace_logger.log_trace_entry` ([`learning/forecast_pipeline_runner.py:152`](learning/forecast_pipeline_runner.py:152)).
*   **Rejection string:** `"❌ Rejected"` and `"❌ Contradictory"` are used to mark forecast status ([`learning/forecast_pipeline_runner.py:93, 111, 267`](learning/forecast_pipeline_runner.py:93)). While descriptive, using constants might be more robust for comparisons.

## Coupling Points
*   **Strong dependence on specific dictionary keys** within forecast objects. Changes to these key names or structures in upstream forecast generation modules would break this pipeline. Examples: `confidence`, `symbolic_tag`, `gpt_output`, `pulse_data`, `gpt_data`, `trace_id`. The use of [`ForecastSchema`](intelligence/forecast_schema.py) for validation in the Epistemic Mirror section ([`learning/forecast_pipeline_runner.py:196-198`](learning/forecast_pipeline_runner.py:196-198)) is a good step towards mitigating this for those specific fields, but this isn't applied to the initial input forecasts.
*   **[`TrustEngine.score_forecast()`](trust_system/trust_engine.py):** The pipeline directly calls this static method.
*   **[`core.pulse_config.USE_SYMBOLIC_OVERLAYS`](core/pulse_config.py):** A global configuration flag directly controls a pipeline step.
*   **External `irldata.variable_recommender` script:** The pipeline relies on this script being available in the Python path and executable via `python -m`.
*   **Implicit assumptions about the output of imported functions:** The pipeline assumes that functions like [`compress_forecasts()`](forecast_output/forecast_compressor.py), [`summarize_forecasts()`](forecast_output/forecast_summary_synthesizer.py), etc., correctly process and return data in the expected format for subsequent steps.
*   **Order of operations:** The sequence of steps is critical. For example, trust scoring happens before compression, and trace ID assignment happens before Epistemic Mirror integration.

## Existing Tests
*   There is no dedicated test file like `tests/test_forecast_pipeline_runner.py` found in the `tests/` directory listing.
*   The module contains a private function [`_test_pipeline()`](learning/forecast_pipeline_runner.py:307-319) which serves as a basic integration test or example usage. This test is simple and uses a small, hardcoded sample of forecasts. It primarily checks if the pipeline runs without crashing and prints the output.
*   **Gaps:**
    *   No comprehensive unit tests for the `run_forecast_pipeline` function itself, testing various scenarios (e.g., empty forecasts, forecasts missing required keys, different configurations of `enable_digest` and `save_to_memory`).
    *   No tests for edge cases or failure modes of individual pipeline steps (though individual component modules might have their own tests).
    *   The existing `_test_pipeline` does not verify the correctness of the output beyond a visual inspection of the printed JSON. Assertions would be needed for proper automated testing.

## Module Architecture and Flow
The module is structured around a single main function, [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54).
**High-level flow:**
1.  **Input Validation:** Checks if forecasts are provided and are in a list format. Basic check for dictionary type for individual forecasts.
2.  **Trust & Fragility Scoring:**
    *   Scores each forecast using [`TrustEngine.score_forecast()`](trust_system/trust_engine.py).
    *   Tags fragility using [`tag_fragility()`](trust_system/fragility_detector.py).
    *   Filters by confidence using [`filter_by_confidence()`](forecast_output/forecast_confidence_gate.py).
    *   Optionally drops rejected forecasts.
3.  **Contradiction Detection:**
    *   Detects contradictions using [`detect_forecast_contradictions()`](forecast_output/forecast_contradiction_detector.py).
    *   Logs contradictions via [`log_learning_event()`](core/pulse_learning_log.py).
    *   Flags involved forecasts as "❌ Contradictory".
4.  **Confidence Gating (Re-applied):** Filters again by confidence.
5.  **Initialization:** Initializes [`TraceMemory`](memory/trace_memory.py) and [`VariablePerformanceTracker`](memory/variable_performance_tracker.py).
6.  **Symbolic Overlays (Conditional):** If `USE_SYMBOLIC_OVERLAYS` is true, attempts to compute and add `arc_label` using [`compute_arc_label()`](symbolic_system/pulse_symbolic_arc_tracker.py).
7.  **Trace Assignment & Registration:**
    *   Assigns trace metadata using [`assign_trace_metadata()`](memory/trace_audit_engine.py).
    *   Registers trace to memory using [`register_trace_to_memory()`](memory/trace_audit_engine.py).
    *   Logs trace entry to [`TraceMemory`](memory/trace_memory.py).
    *   Logs variable contribution to [`VariablePerformanceTracker`](memory/variable_performance_tracker.py).
8.  **Epistemic Mirror Integration:** For each forecast:
    *   Extracts rules, arcs, missing domains from GPT output.
    *   Extracts and archives causal fingerprints from GPT rationale.
    *   Computes symbolic convergence loss between Pulse and GPT data (requires [`ForecastSchema`](intelligence/forecast_schema.py) validation).
    *   Tags and logs forecast divergence.
9.  **Forecast Compression:** Compresses forecasts using [`compress_forecasts()`](forecast_output/forecast_compressor.py).
10. **Symbolic Summarization:** Summarizes compressed forecasts using [`summarize_forecasts()`](forecast_output/forecast_summary_synthesizer.py).
11. **Digest Generation (Conditional):** If `enable_digest` is true, builds a digest using [`build_digest()`](forecast_output/strategos_digest_builder.py).
12. **Memory Store (Conditional):** If `save_to_memory` is true, stores compressed forecasts in [`ForecastMemory`](memory/forecast_memory.py).
13. **Top Forecast Selection & Export:**
    *   Selects top N forecasts using [`select_top_forecasts()`](forecast_output/forecast_prioritization_engine.py).
    *   Exports them to `logs/strategic_batch_output.jsonl`.
    *   Selects promotable forecasts from the top N using [`select_promotable_forecasts()`](memory/forecast_memory_promoter.py).
    *   Exports promotable forecasts to memory using [`export_promoted()`](memory/forecast_memory_promoter.py).
14. **Logging & Reporting:**
    *   Logs count of rejected forecasts.
    *   Logs [`TraceMemory`](memory/trace_memory.py) summary.
    *   Exports variable scores via [`VariablePerformanceTracker`](memory/variable_performance_tracker.py).
15. **Automated Variable Recommendation:** Executes `irldata.variable_recommender` as a subprocess.
16. **Return Results:** Bundles status, counts, digest, and top forecasts into a result dictionary.
17. **Capital Layer (Commented Out):** Placeholder for adding capital exposure and alignment summaries if state were available.

Error handling is generally done with `try-except` blocks around major stages, logging errors and often returning an error status or continuing with potentially partial data.

## Naming Conventions
*   **Functions:** Generally follow PEP 8 (snake_case, e.g., [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:54), [`_test_pipeline()`](learning/forecast_pipeline_runner.py:307)).
*   **Variables:** Mostly snake_case (e.g., `batch_id`, `enable_digest`, `scored`, `compressed`). Some shorter variables like `f` for forecast in loops are used, which is common. `div_type` ([`learning/forecast_pipeline_runner.py:208`](learning/forecast_pipeline_runner.py:208)) is a slight abbreviation. There's a typo `diverggence_type` ([`learning/forecast_pipeline_runner.py:209, 213, 215`](learning/forecast_pipeline_runner.py:209)) which should be `divergence_type`.
*   **Classes:** Imported classes use PascalCase (e.g., [`TrustEngine`](trust_system/trust_engine.py), [`ForecastMemory`](memory/forecast_memory.py), [`ForecastSchema`](intelligence/forecast_schema.py)), which is standard.
*   **Constants:** `USE_SYMBOLIC_OVERLAYS` ([`learning/forecast_pipeline_runner.py:18`](learning/forecast_pipeline_runner.py:18)) is uppercase, following PEP 8.
*   **Module Name:** `forecast_pipeline_runner.py` is descriptive and follows snake_case.
*   **Comments:** Comments like `# Step 1: Score trust + fragility` ([`learning/forecast_pipeline_runner.py:83`](learning/forecast_pipeline_runner.py:83)) clearly delineate pipeline stages.
*   **Potential AI Assumption Errors/Deviations:**
    *   The typo `diverggence_type` is a minor deviation.
    *   The author tag "Pulse v0.23" ([`learning/forecast_pipeline_runner.py:14`](learning/forecast_pipeline_runner.py:14)) might be an AI-generated placeholder or a convention within this project.
    *   The structure of comments and logging messages is generally consistent and human-readable.

Overall, naming conventions are largely consistent with Python best practices (PEP 8).