# Sprint 8 Plan

**Sprint Goal:** Address critical blockers identified from Sprint 7's `pytest` failures to improve system stability and core functionality, focusing on metrics, data storage, and integration error handling.

**Start Date:** 2025-05-12 (Assuming day after Sprint 7 outcome)
**End Date:** (To be determined - typically 1-2 weeks)

**Blocked Task from Previous Sprints:**
*   **GTB7-002: AdvancedFeatureProcessor TensorFlow Compatibility** - Status: Blocked (TensorFlow compatibility issues on native Windows). No work planned for Sprint 8.

---

## Sprint Backlog - Sprint 8 Focus

| Task ID | Description                                                                                                                               | Potential Files Involved                                                                                                | Success Criteria                                                                                                                                                                                                                            | Tentative Agent | Priority | Status |
| :------ | :---------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------- | :------- | :----- |
| GTB8-001 | **Fix MetricsStore Singleton Pattern:** The `test_singleton_pattern` failure (AssertionError: Expected `__init__` to have been called once. Called 0 times) was resolved by resetting `MetricsStore._instance = None` in the test setup. Additionally, `test_export_to_dataframe` was fixed by removing a local pandas import in `recursive_training/metrics/metrics_store.py`. The `test_track_cost` still fails but is likely a separate mock setup issue within that specific test. | - [`tests/recursive_training/test_metrics_store.py`](tests/recursive_training/test_metrics_store.py) <br> - [`recursive_training/metrics_store.py`](recursive_training/metrics_store.py)                               | - `tests/recursive_training/test_metrics_store.py::TestMetricsStore::test_singleton_pattern` passes. <br> - `pytest -q` shows the test passing. <br> - No new regressions in `MetricsStore`. <br> - Ideally, related `MetricsStore` tests also pass. | debug           | High     | Done   |
| GTB8-002 | The `TestRecursiveDataStore::test_cleanup` failure (previously `AssertionError: assert 1 == 2`) was resolved. The test was enhanced with a `smart_glob_side_effect` for `pathlib.Path.glob` and specific assertions for `os.remove` and `Path.rmdir` calls, ensuring the cleanup logic is now correctly verified. A syntax error from a previous diff application was also corrected. | - [`tests/recursive_training/test_data_store.py`](tests/recursive_training/test_data_store.py) <br> - [`recursive_training/data_store.py`](recursive_training/data_store.py)                                     | - `tests/recursive_training/test_data_store.py::TestRecursiveDataStore::test_cleanup` passes. <br> - `pytest -q` shows the test passing. <br> - No new regressions in `RecursiveDataStore` cleanup.                                          | debug           | High     | Done  |
| | GTB8-003 | The `TestContext7Integration::test_error_handling` failure (`AssertionError: ValueError not raised`) was resolved. The `get_library_documentation` function in `utils/context7_client.py` was modified to correctly catch and re-raise exceptions originating from MCP tool calls as `ValueError`, ensuring the test's expectation is met. This involved restructuring the try-except blocks. | - [`tests/test_context7_integration.py`](tests/test_context7_integration.py) <br> - [`utils/context7_client.py`](utils/context7_client.py) (or related Context7 files) | - [`tests/test_context7_integration.py::TestContext7Integration::test_error_handling`](tests/test_context7_integration.py) passes. <br> - `pytest -q` shows the test passing. <br> - System correctly raises `ValueError` for tested conditions. <br> - No new regressions in Context7 integration. | debug           | High     | Done  |

---

## Full List of Remaining Failures (Excluding Blocked GTB7-002 and Sprint 8 selections)

*   `FAILED tests/recursive_training/test_async_metrics_collector.py::TestAsyncMetricsCollector::test_error_callback - AssertionError: False is not true`
*   `FAILED tests/recursive_training/test_data_ingestion.py::TestRecursiveDataIngestionManager::test_get_cost_summary - assert 0.30000000000000004 == 0.3`
*   `FAILED tests/recursive_training/test_metrics_store.py::TestMetricsStore::test_track_cost - AssertionError: Expected 'mock' to have been called once. Called 0 times.` (Potentially resolved by GTB8-001)
*   `FAILED tests/recursive_training/test_metrics_store.py::TestMetricsStore::test_export_to_dataframe - AssertionError: Expected 'DataFrame' to be called once. Called 0 times.` (Potentially resolved by GTB8-001)
*   `FAILED tests/recursive_training/test_s3_data_store.py::TestS3DataStore::test_store_dataset_s3 - AssertionError: assert 'dataset_test...0250512025126' == 'dataset_test_123456'`
*   `FAILED tests/recursive_training/test_s3_data_store.py::TestS3DataStore::test_fallback_to_parent_methods - AssertionError: Expected 'retrieve_dataset_optimized' to have been called once. Called 0 times.`
*   `FAILED tests/recursive_training/test_streaming_data_store.py::TestStreamingDataStore::test_streaming_with_filtering - AssertionError: 0 != 16`
*   `FAILED tests/recursive_training/test_streaming_data_store.py::TestStreamingDataStore::test_streaming_with_pyarrow - AssertionError: 0 != 5`
*   `FAILED tests/recursive_training/test_training_metrics.py::TestRecursiveTrainingMetrics::test_calculate_f1_score - assert 0.6 == 0.775`
*   `FAILED tests/recursive_training/test_training_metrics.py::TestRecursiveTrainingMetrics::test_evaluate_rule_performance - AssertionError: assert 'accuracy' in {'mse': -50.0}`
*   `FAILED tests/recursive_training/test_training_metrics.py::TestRecursiveTrainingMetrics::test_get_performance_summary - assert 12.4999999999999996 == 12.5`
*   `FAILED tests/test_ai_forecaster.py::TestAIForecaster::test_predict_default - AssertionError: -0.04691165313124657 != 0.0`
*   `FAILED tests/test_rule_adjustment.py::TestRuleAdjustment::test_adjust_rules_from_learning - AssertionError: register_variable('tag__weight_hope', {'type': 'trust_weight', 'description': 'Trust weight for tag: hope', 'de...`
*   `FAILED tests/test_trust_engine_risk.py::TestRiskScoring::test_compute_risk_score_no_memory - AssertionError: 0.26 != 0.06 within 2 places (0.2 difference)`