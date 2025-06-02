# Module Analysis: `operator_interface/strategos_digest.py`

## 1. Module Intent/Purpose

The primary role of the [`operator_interface/strategos_digest.py`](operator_interface/strategos_digest.py) module is to generate a comprehensive "Strategos Digest." This digest serves as a detailed summary report of recent forecasts, designed for an operator or analyst. It consolidates various aspects of the forecasting system's performance and state, including:

*   Forecast licensing and trust enforcement metrics.
*   Alignment scores and confidence levels of forecasts.
*   Symbolic learning insights, including learning profiles and upgrade plans.
*   Drift analysis, covering both symbolic arc drift and simulation state drift.
*   Narrative cluster classifications.
*   Visualization of symbolic transitions and mutation trajectories.
*   Summaries of rule cluster activity.

The module aims to provide a multi-faceted overview to help understand the system's current operational status, identify potential issues (like high license loss or significant drift), and highlight key strategic forecasts.

## 2. Operational Status/Completeness

*   **Status:** Largely operational and actively developed, with many features integrated.
*   **Completeness:** While extensive, there are areas marked for future implementation.
    *   Numerous "PATCH" comments (e.g., [`operator_interface/strategos_digest.py:23`](operator_interface/strategos_digest.py:23), [`operator_interface/strategos_digest.py:283`](operator_interface/strategos_digest.py:283)) indicate ongoing additions and refinements.
    *   **Placeholders/TODOs:**
        *   [`_extract_symbolic_flip_patterns()`](operator_interface/strategos_digest.py:135) contains a `TODO: Implement actual pattern detection` ([`operator_interface/strategos_digest.py:139`](operator_interface/strategos_digest.py:139)).
        *   [`_extract_detected_loops()`](operator_interface/strategos_digest.py:142) contains a `TODO: Implement actual loop detection` ([`operator_interface/strategos_digest.py:146`](operator_interface/strategos_digest.py:146)).
    *   **Commented-out Imports:**
        *   `# from forecast_output.forecast_compressor import compress_forecasts` ([`operator_interface/strategos_digest.py:4`](operator_interface/strategos_digest.py:4))
        *   `# from symbolic_system.pulse_symbolic_revision_planner import plan_revisions_for_fragmented_arcs` ([`operator_interface/strategos_digest.py:18`](operator_interface/strategos_digest.py:18))
        These suggest features that might have been considered, removed, or are pending integration.
## 3. Implementation Gaps / Unfinished Next Steps

*   **Explicit TODOs:** The primary gaps are the unimplemented symbolic flip pattern detection and loop detection functionalities as noted above.
*   **Potential Extensions:**
    *   The comment `Optionally call symbolic audit system or arc drift scanner here` ([`operator_interface/strategos_digest.py:203`](operator_interface/strategos_digest.py:203)) within the license loss warning logic suggests a point for future automation or deeper diagnostic triggering.
*   **Modularization:** The main function, [`generate_strategos_digest()`](operator_interface/strategos_digest.py:149), is very long and handles many distinct sections of the digest. Breaking it down into smaller, more focused helper functions for each digest section could improve readability and maintainability.
*   The features related to the commented-out imports ([`forecast_compressor`](forecast_output/forecast_compressor.py) and [`pulse_symbolic_revision_planner`](symbolic_system/pulse_symbolic_revision_planner.py)) represent potential areas for future development or re-integration.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`forecast_output.forecast_licenser`](forecast_output/forecast_licenser.py): [`filter_licensed_forecasts()`](forecast_output/forecast_licenser.py:filter_licensed_forecasts)
*   [`forecast_output.strategos_tile_formatter`](forecast_output/strategos_tile_formatter.py): [`format_strategos_tile()`](forecast_output/strategos_tile_formatter.py:format_strategos_tile)
*   [`forecast_output.strategos_digest_builder`](forecast_output/strategos_digest_builder.py): [`build_digest()`](forecast_output/strategos_digest_builder.py:build_digest), [`filter_forecasts_by_prompt()`](forecast_output/strategos_digest_builder.py:filter_forecasts_by_prompt)
*   [`analytics.forecast_memory`](memory/forecast_memory.py): [`ForecastMemory`](memory/forecast_memory.py:ForecastMemory)
*   [`core.path_registry`](core/path_registry.py): [`PATHS`](core/path_registry.py:PATHS)
*   [`trust_system.alignment_index`](trust_system/alignment_index.py): [`compute_alignment_index()`](trust_system/alignment_index.py:compute_alignment_index)
*   [`trust_system.forecast_episode_logger`](trust_system/forecast_episode_logger.py): [`summarize_episodes()`](trust_system/forecast_episode_logger.py:summarize_episodes)
*   [`trust_system.trust_engine`](trust_system/trust_engine.py): [`compute_symbolic_attention_score()`](trust_system/trust_engine.py:compute_symbolic_attention_score)
*   [`trust_system.forecast_licensing_shell`](trust_system/forecast_licensing_shell.py): [`license_forecast()`](trust_system/forecast_licensing_shell.py:license_forecast)
*   [`engine.simulation_drift_detector`](simulation_engine/simulation_drift_detector.py): [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:run_simulation_drift_analysis)
*   [`trust_system.license_enforcer`](trust_system/license_enforcer.py): [`annotate_forecasts()`](trust_system/license_enforcer.py:annotate_forecasts), [`filter_licensed()`](trust_system/license_enforcer.py:filter_licensed), [`summarize_license_distribution()`](trust_system/license_enforcer.py:summarize_license_distribution)
*   [`forecast_output.mutation_compression_engine`](forecast_output/mutation_compression_engine.py): [`compress_episode_chain()`](forecast_output/mutation_compression_engine.py:compress_episode_chain), [`plot_symbolic_trajectory()`](forecast_output/mutation_compression_engine.py:plot_symbolic_trajectory)
*   [`analytics.forecast_episode_tracer`](memory/forecast_episode_tracer.py): [`build_episode_chain()`](memory/forecast_episode_tracer.py:build_episode_chain)
*   [`symbolic_system.symbolic_transition_graph`](symbolic_system/symbolic_transition_graph.py): [`build_symbolic_graph()`](symbolic_system/symbolic_transition_graph.py:build_symbolic_graph), [`visualize_symbolic_graph()`](symbolic_system/symbolic_transition_graph.py:visualize_symbolic_graph)
*   [`forecast_output.forecast_resonance_scanner`](forecast_output/forecast_resonance_scanner.py): [`generate_resonance_summary()`](forecast_output/forecast_resonance_scanner.py:generate_resonance_summary)
*   [`forecast_output.forecast_fidelity_certifier`](forecast_output/forecast_fidelity_certifier.py): [`generate_certified_digest()`](forecast_output/forecast_fidelity_certifier.py:generate_certified_digest)
*   [`forecast_output.forecast_prioritization_engine`](forecast_output/forecast_prioritization_engine.py): [`select_top_forecasts()`](forecast_output/forecast_prioritization_engine.py:select_top_forecasts)
*   [`forecast_output.forecast_cluster_classifier`](forecast_output/forecast_cluster_classifier.py): [`classify_forecast_cluster()`](forecast_output/forecast_cluster_classifier.py:classify_forecast_cluster), [`summarize_cluster_counts()`](forecast_output/forecast_cluster_classifier.py:summarize_cluster_counts)
*   [`operator_interface.rule_cluster_digest_formatter`](operator_interface/rule_cluster_digest_formatter.py): [`format_cluster_digest_md()`](operator_interface/rule_cluster_digest_formatter.py:format_cluster_digest_md)
*   [`symbolic_system.pulse_symbolic_learning_loop`](symbolic_system/pulse_symbolic_learning_loop.py): [`generate_learning_profile()`](symbolic_system/pulse_symbolic_learning_loop.py:generate_learning_profile), [`learn_from_tuning_log()`](symbolic_system/pulse_symbolic_learning_loop.py:learn_from_tuning_log)
*   [`symbolic_system.symbolic_upgrade_planner`](symbolic_system/symbolic_upgrade_planner.py): [`propose_symbolic_upgrades()`](symbolic_system/symbolic_upgrade_planner.py:propose_symbolic_upgrades)
*   [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py): [`rewrite_forecast_symbolics()`](symbolic_system/symbolic_executor.py:rewrite_forecast_symbolics)
*   [`trust_system.recovered_forecast_scorer`](trust_system/recovered_forecast_scorer.py): [`summarize_repair_quality()`](trust_system/recovered_forecast_scorer.py:summarize_repair_quality)

### External Library Dependencies:
*   `logging`
*   `typing`
*   `matplotlib.pyplot`
*   `os`
*   `json`
*   `unittest` (used for inline tests)

### Shared Data Interactions:
*   **Reads from:**
    *   `ForecastMemory` instance.
    *   Episode log files (paths provided as arguments).
    *   Simulation trace files (paths provided as arguments).
    *   [`logs/tuning_results.jsonl`](logs/tuning_results.jsonl) ([`operator_interface/strategos_digest.py:243`](operator_interface/strategos_digest.py:243))
    *   [`forecasts/revision_candidates.jsonl`](forecasts/revision_candidates.jsonl) ([`operator_interface/strategos_digest.py:273`](operator_interface/strategos_digest.py:273))
*   **Writes to (Output Files):**
    *   Generates image files for plots:
        *   `plots/symbolic_trajectory_{root_id}.png` ([`operator_interface/strategos_digest.py:431`](operator_interface/strategos_digest.py:431))
        *   `plots/strategos_symbolic_graph.png` ([`operator_interface/strategos_digest.py:447`](operator_interface/strategos_digest.py:447))
    *   The main output is a Markdown formatted string (the digest itself).
## 5. Function and Class Example Usages

*   **[`generate_strategos_digest(memory: ForecastMemory, n: int = 5, ...)`](operator_interface/strategos_digest.py:149):**
    *   This is the core function for generating the detailed Markdown digest.
    *   **Usage:** `digest_string = generate_strategos_digest(forecast_memory_instance, n=10, title="Cycle 12 Digest", previous_episode_log="path/to/prev_log.jsonl", current_episode_log="path/to/curr_log.jsonl")`

*   **[`live_digest_ui(memory: ForecastMemory, prompt: Optional[str] = None, ...)`](operator_interface/strategos_digest.py:582):**
    *   Provides a simpler digest, possibly for a more interactive UI, using [`build_digest()`](forecast_output/strategos_digest_builder.py:build_digest) from another module.
    *   **Usage:** `ui_output = live_digest_ui(forecast_memory_instance, prompt="economic indicators", n=5, export_fmt="markdown", template="summary")`

*   **Helper Functions:**
    *   [`group_by_confidence(forecasts_list)`](operator_interface/strategos_digest.py:48): Internally used to categorize forecasts.
    *   [`compute_arc_drift(prev_log_path, curr_log_path)`](operator_interface/strategos_digest.py:75): Internally used if log paths are provided.
    *   [`flag_drift_sensitive_forecasts(forecasts_list, drift_report_dict)`](operator_interface/strategos_digest.py:100): Internally used if drift analysis is run.

*   **Inline Test ([`_test_digest()`](operator_interface/strategos_digest.py:617)):**
    ```python
    # From _test_digest()
    import unittest
    class DummyMemory(ForecastMemory):
        def get_recent(self, n, domain=None, default=None):
            return [
                {"confidence": 0.8, "alignment_score": 80, "trust_label": "🟢 Trusted", ...},
                # ... more dummy data ...
            ]

    digest = generate_strategos_digest(DummyMemory(), n=3, title="Test Digest")
    # Assertions follow to check digest content
    ```

## 6. Hardcoding Issues

*   **File Paths:**
    *   `tuning_log = "logs/tuning_results.jsonl"` ([`operator_interface/strategos_digest.py:243`](operator_interface/strategos_digest.py:243)).
    *   `upgrade_log = "plans/symbolic_upgrade_plan.json"` ([`operator_interface/strategos_digest.py:260`](operator_interface/strategos_digest.py:260)) (Note: this path is read from, its creation is external).
    *   `"forecasts/revision_candidates.jsonl"` ([`operator_interface/strategos_digest.py:273`](operator_interface/strategos_digest.py:273)).
    *   The output directory for plots, `"plots/"`, is hardcoded in [`os.path.join()`](operator_interface/strategos_digest.py:431,447) calls. These should ideally be managed via the [`PATHS`](core/path_registry.py:PATHS) registry.
*   **Default Directory:** `DIGEST_DIR` defaults to `PATHS["WORLDSTATE_LOG_DIR"]` if not found in `PATHS` ([`operator_interface/strategos_digest.py:36`](operator_interface/strategos_digest.py:36)).
*   **Thresholds & Magic Numbers:**
    *   Confidence grouping thresholds (0.75, 0.5) in [`group_by_confidence()`](operator_interface/strategos_digest.py:62-67).
    *   Drift flagging threshold (0.2) in [`flag_drift_sensitive_forecasts()`](operator_interface/strategos_digest.py:103).
    *   License loss warning threshold (40%) ([`operator_interface/strategos_digest.py:199`](operator_interface/strategos_digest.py:199)).
    *   `top_n=5` for `select_top_forecasts` call ([`operator_interface/strategos_digest.py:301`](operator_interface/strategos_digest.py:301)).
    *   `limit=3` for `format_cluster_digest_md` call ([`operator_interface/strategos_digest.py:578`](operator_interface/strategos_digest.py:578)).
*   **Placeholder Data:** The return values in [`_extract_symbolic_flip_patterns()`](operator_interface/strategos_digest.py:140) and [`_extract_detected_loops()`](operator_interface/strategos_digest.py:147) are hardcoded examples.
## 7. Coupling Points

*   **Data Structures:** Highly coupled to the specific dictionary structure of forecast objects (keys like `confidence`, `trace_id`, `arc_label`, `fired_rules`, `symbolic_change`, `alignment_score`, `license_status`, etc.). Changes to this structure elsewhere could break the digest generation.
*   **Module APIs:** Tightly coupled with the APIs of numerous imported modules from `forecast_output`, `trust_system`, `symbolic_system`, `memory`, and `simulation_engine`. Changes in the function signatures or return types of these dependencies would require updates here.
*   **[`PATHS`](core/path_registry.py:PATHS) Registry:** Relies on [`PATHS`](core/path_registry.py:PATHS) for some directory configurations.
*   **File Formats:** Implicitly depends on the format of external files it reads (e.g., `tuning_results.jsonl`, episode logs, simulation traces).

## 8. Existing Tests

*   An inline test suite is present within the module, defined in the [`_test_digest()`](operator_interface/strategos_digest.py:617) function and `StrategosDigestTest` class.
*   This test uses a `DummyMemory` class to provide mock forecast data.
*   It primarily checks if the main [`generate_strategos_digest()`](operator_interface/strategos_digest.py:149) function runs and if key sections/titles are present in the output.
*   **Coverage:** This provides a basic integration test for the happy path of the main digest generation. It does not offer granular unit tests for helper functions or cover many edge cases (e.g., missing optional files, malformed forecast data beyond a simple empty dict, errors from dependencies).
*   No evidence of a dedicated test file like `tests/test_operator_interface_strategos_digest.py` in the provided file list, though `tests/test_digest_exporter.py` might have some relevance. A more comprehensive, separate test suite would be beneficial given the module's complexity.
## 9. Module Architecture and Flow

The module's primary function is [`generate_strategos_digest()`](operator_interface/strategos_digest.py:149). Its flow is as follows:

1.  **Data Retrieval & Initial Processing:**
    *   Fetches recent forecasts from a `ForecastMemory` instance.
    *   Applies licensing filters ([`filter_licensed_forecasts()`](forecast_output/forecast_licenser.py:filter_licensed_forecasts)).
2.  **Trust & Licensing Analysis:**
    *   Annotates forecasts and filters by license status ([`annotate_forecasts()`](trust_system/license_enforcer.py:annotate_forecasts), [`filter_licensed()`](trust_system/license_enforcer.py:filter_licensed)).
    *   Calculates license drop rate and summarizes distribution.
    *   Computes alignment scores ([`compute_alignment_index()`](trust_system/alignment_index.py:compute_alignment_index)).
    *   Determines individual forecast license status ([`license_forecast()`](trust_system/forecast_licensing_shell.py:license_forecast)).
3.  **Symbolic & Narrative Analysis:**
    *   Builds and compresses episode chains ([`build_episode_chain()`](memory/forecast_episode_tracer.py:build_episode_chain), [`compress_episode_chain()`](forecast_output/mutation_compression_engine.py:compress_episode_chain)).
    *   Integrates symbolic learning profiles and upgrade plans by processing `tuning_log` and `revision_candidates.jsonl` (using functions from `symbolic_system`).
    *   Generates symbolic resonance summaries ([`generate_resonance_summary()`](forecast_output/forecast_resonance_scanner.py:generate_resonance_summary)).
    *   Creates forecast certification digests ([`generate_certified_digest()`](forecast_output/forecast_fidelity_certifier.py:generate_certified_digest)).
    *   Classifies forecasts into narrative clusters ([`classify_forecast_cluster()`](forecast_output/forecast_cluster_classifier.py:classify_forecast_cluster)).
    *   Selects top strategic forecasts ([`select_top_forecasts()`](forecast_output/forecast_prioritization_engine.py:select_top_forecasts)).
4.  **Drift Analysis (Conditional):**
    *   If previous/current episode logs are provided, computes arc drift ([`compute_arc_drift()`](operator_interface/strategos_digest.py:75)).
    *   If previous/current simulation traces are provided, runs simulation drift analysis ([`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:run_simulation_drift_analysis)) and flags sensitive forecasts ([`flag_drift_sensitive_forecasts()`](operator_interface/strategos_digest.py:100)).
5.  **Markdown Digest Assembly:**
    *   Sequentially constructs the Markdown output string by adding sections for each analysis type (Top Strategic Forecasts, Trust Report, Licensing, Certification, Narrative Clusters, Drift, Mutation Episodes, Symbolic Graph, Resonance, Tuning, Flip Patterns, Loops).
    *   Formats individual forecast "tiles" using [`format_strategos_tile()`](forecast_output/strategos_tile_formatter.py:format_strategos_tile), grouped by confidence ([`group_by_confidence()`](operator_interface/strategos_digest.py:48)).
    *   Includes aggregate statistics (scores, age, sparklines).
    *   Appends a rule cluster digest ([`format_cluster_digest_md()`](operator_interface/rule_cluster_digest_formatter.py:format_cluster_digest_md)).
6.  **Visualizations:**
    *   Generates and saves plots for symbolic trajectories ([`plot_symbolic_trajectory()`](forecast_output/mutation_compression_engine.py:plot_symbolic_trajectory)) and the symbolic transition graph ([`visualize_symbolic_graph()`](symbolic_system/symbolic_transition_graph.py:visualize_symbolic_graph)), embedding them in the Markdown.
7.  **Supporting Functions:**
    *   [`live_digest_ui()`](operator_interface/strategos_digest.py:582): Provides an alternative digest generation path, likely for a simpler UI, using [`build_digest()`](forecast_output/strategos_digest_builder.py:build_digest).
    *   Various helper functions for specific tasks like saving plots, grouping forecasts, etc.

## 10. Naming Conventions

*   **PEP 8 Adherence:** Generally follows PEP 8 standards. Functions and variables use `snake_case` (e.g., [`generate_strategos_digest`](operator_interface/strategos_digest.py:149), `licensed_count`). Classes use `CapWords` (e.g., [`ForecastMemory`](memory/forecast_memory.py:ForecastMemory), `StrategosDigestTest`). Constants are `UPPER_CASE` (e.g., `DIGEST_DIR`).
*   **Descriptiveness:** Names are mostly descriptive and clear (e.g., `compute_arc_drift`, `flag_drift_sensitive_forecasts`).
*   **Abbreviations:** Some local-scope abbreviations are used (e.g., `fc` for forecast, `ce` for compressed episode, `sts` for symbolic tuning summary), which is generally acceptable for brevity.
*   **Internal/Test Functions:** Prefixed with an underscore (e.g., [`_extract_symbolic_flip_patterns`](operator_interface/strategos_digest.py:135), [`_test_digest`](operator_interface/strategos_digest.py:617)), correctly indicating their intended use.
*   **"PATCH" Comments:** A consistent convention of using `--- PATCH: ---` comments to mark areas of recent changes or additions.
*   **Emoji Usage:** Emojis are used in the generated Markdown for section headers (e.g., "📘", "🛡️") and confidence labels (e.g., "🟢 Trusted"). This is a stylistic choice for the output format.
*   No obvious AI assumption errors or significant deviations from common Python naming standards were noted.