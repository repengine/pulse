# Triage & Issue Extraction Plan

## Goal
Build an authoritative inventory of modules that need work by parsing `docs/pulse_inventory.md` and its companion markdown files. Then, generate a Python script (`dev_tools/triage/build_triage_report.py`) that outputs this inventory as a JSON report.

## Status
- [ ] Planning phase initiated.
- [x] `docs/pulse_inventory.md` parsing logic defined (implemented in build_triage_report.py).
- [x] Companion markdown parsing logic defined (implemented in build_triage_report.py).
- [x] Python script `dev_tools/triage/build_triage_report.py` generation logic defined (implemented in script).
- [x] Python script `dev_tools/triage/build_triage_report.py` created.
- [x] Final JSON report generated.

## Decisions & Actions Log
- Orchestrator initiated Think mode for planning.
- Code mode created this planning document.
- Code mode created dev_tools/triage/build_triage_report.py with parsing and JSON generation logic.
- Code mode updated this planning document.
- Code mode executed dev_tools/triage/build_triage_report.py.
- Code mode updated this planning document.

{
  "GPT/gpt_causal_translator.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "GPT/gpt_forecast_divergence_logger.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "GPT/gpt_rule_fingerprint_extractor.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "GPT/gpt_symbolic_convergence_loss.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "__init__.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "adapters/core_adapter.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "There are no obvious placeholders, TODOs, or comments suggesting unfinished work within this specific module."
  },
  "adapters/simulation_adapter.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "There are no obvious placeholders or TODOs."
  },
  "adapters/symbolic_adapter.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "No TODOs or obvious placeholders are present."
  },
  "adapters/trust_adapter.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "No explicit TODOs or placeholders are visible."
  },
  "analyze_historical_data_quality.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "No explicit \"TODO\" comments or obvious placeholders for core functionality were observed."
  },
  "api/core_api.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "- **Configuration:** API host, port, and debug mode are hardcoded for development."
  },
  "api/server.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "- No obvious TODOs are marked in comments, but the placeholder comments clearly indicate unfinished sections."
  },
  "api_key_report.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "- There are no obvious `TODO`, `FIXME`, or placeholder comments indicating unfinished sections."
  },
  "api_key_test.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "api_key_test_updated.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "benchmark_retrodiction.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "- No explicit `TODO` comments or obvious major placeholders were identified."
  },
  "capital_engine/__init__.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "capital_engine/capital_digest_formatter.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "## Hardcoding Issues\n- Markdown headings and default/fallback strings are hardcoded (generally acceptable for fixed reports)."
  },
  "capital_engine/capital_layer.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "capital_engine/capital_layer_cli.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "## Implementation Gaps / Unfinished Next Steps\n- **Command-Line Arguments:** Uses hardcoded `mock_vars`."
  },
  "causal_model/counterfactual_engine.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "causal_model/counterfactual_simulator.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "causal_model/discovery.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "causal_model/optimized_discovery.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "causal_model/structural_causal_model.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "causal_model/vectorized_operations.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/config/llm_config.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/conversational_core.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/integrations/pulse_module_adapters.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/launch_conversational_ui.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "There are no obvious placeholders or TODO comments within the code."
  },
  "chatmode/llm_integration/domain_adapter.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/llm_integration/llm_model.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/llm_integration/openai_config.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/rag/__init__.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/rag/context_provider.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/test_openai_integration.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/ui/conversational_gui.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/vector_store/build_vector_store.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/vector_store/codebase_parser.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "chatmode/vector_store/codebase_vector_store.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "check_benchmark_deps.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "- There are no obvious placeholders, `TODO` comments, or unfinished sections within the script."
  },
  "cli/gui_launcher.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "1:5002/api/status` is hardcoded in [`wait_for_api_server()`](cli/gui_launcher."
  },
  "cli/interactive_shell.py": {
    "status": "needs_fix",
    "source": "inventory",
    "issue_excerpt": "Provides a strategist shell for Pulse interaction with several unimplemented commands marked as stubs, indicating planned but incomplete functionality."
  },
  "cli/main.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "*   Paths for epistemic upgrade plans and related files (`upgrade_path`, `batch_path`, `revised_path`) are retrieved from the loaded `CONFIG` object or use hard"
  },
  "config/": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "config/ai_config.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "py:10) is currently hardcoded."
  },
  "config/gravity_config.py": {
    "status": "needs_fix",
    "source": "inventory",
    "issue_excerpt": "Provides a comprehensive set of hardcoded default constants for the Residual-Gravity Overlay system, covering core parameters, safety thresholds, feature flags,"
  },
  "conftest.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "There are no obvious placeholders or TODO comments within the provided code."
  },
  "core/__init__.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "core/bayesian_trust_tracker.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "0`) are hardcoded in [`self."
  },
  "core/celery_app.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "py:1) instead of relying solely on environment variables or hardcoded defaults."
  },
  "core/event_bus.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "core/feature_store.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "While this centralizes configuration, the path itself is hardcoded."
  },
  "core/metrics.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "*   **Testability:** While simple, the module lacks tests."
  },
  "core/module_registry.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "core/optimized_trust_tracker.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "py:41)) is hardcoded; making it configurable could offer more flexibility."
  },
  "core/path_registry.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "log\" are hardcoded and cannot be easily changed without modifying the code."
  },
  "core/pulse_config.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "yaml\", \"host\", \"localhost\")\n```\n\n## Hardcoding Issues\n\nSeveral hardcoded values are present:\n\n1."
  },
  "core/pulse_learning_log.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "core/schemas.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "core/service_registry.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": ") are hardcoded strings."
  },
  "core/training_review_store.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "py:19) is hardcoded."
  },
  "core/trust_update_buffer.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "Hardcoding Issues\n\n- **Default Configuration Values:** Default values for `max_buffer_size`, `flush_threshold`, and `auto_flush_interval_sec` are hardcoded with"
  },
  "core/variable_accessor.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "0 (assuming \"gdp\" is not in VARIABLE_REGISTRY)\n    ```\n*   **Hardcoding Issues**:\n    *   The default value for missing variables/overlays in getter functions i"
  },
  "core/variable_registry.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "Key Functionalities\n\n*   **Static Variable Definitions**: A large, hardcoded dictionary `VARIABLE_REGISTRY` ([`core/variable_registry."
  },
  "dags/": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "dags/retrodiction_dag.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "data/": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": ", API endpoints, default date ranges, retry parameters) are often hardcoded within scripts."
  },
  "data/ground_truth_generator.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "*   **Implementation Gaps / Unfinished Next Steps:**\n    *   **NASDAQ API Integration:** Explicitly marked as \"TODO\" ([`data/ground_truth_generator."
  },
  "data/ground_truth_ingestion_manager.py": {
    "status": "no_known_issues",
    "source": "none",
    "issue_excerpt": ""
  },
  "data/high_frequency_data_access.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "*   **Configuration:** Data format (JSON key for timestamp, timestamp format) is hardcoded."
  },
  "data/high_frequency_data_store.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "jsonl\n```\n\n### Hardcoding Issues\n*   The default `base_dir` is hardcoded to [`\"data/high_frequency_data\"`](data/high_frequency_data_store."
  },
  "data/identify_unmapped_variables.py": {
    "status": "needs_fix",
    "source": "companion_md",
    "issue_excerpt": "## Hardcoding Issues\n- The script uses a hardcoded path to the `VARIABLE_REGISTRY` ([`core/variable_registry."
  }
}
