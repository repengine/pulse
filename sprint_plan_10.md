# Sprint 10 Plan

**Sprint Goal:** Continue to reduce the number of failing tests by addressing issues in the `recursive_training` module, specifically focusing on `AdvancedFeatureProcessor` and `RecursiveDataIngestionManager`.

**Start Date:** 2025-05-12
**End Date:** (To be determined)

---

## Sprint Backlog - Selected Blockers

### Task GTB10-001
*   **Description:** The `test_process` failure (mock for `apply_time_frequency_decomposition` not called) was resolved. The `unittest.mock.patch` decorators in [`tests/recursive_training/test_advanced_feature_processor.py`](tests/recursive_training/test_advanced_feature_processor.py) were updated to correctly target the functions where they are imported and used within the `recursive_training.data.advanced_feature_processor` module.
*   **Potential Files Involved:**
    *   [`tests/recursive_training/test_advanced_feature_processor.py`](tests/recursive_training/test_advanced_feature_processor.py)
    *   [`recursive_training/data/advanced_feature_processor.py`](recursive_training/data/advanced_feature_processor.py)
    *   [`recursive_training/data/time_frequency_decomposition.py`](recursive_training/data/time_frequency_decomposition.py)
*   **Success Criteria:**
    *   [`tests/recursive_training/test_advanced_feature_processor.py::TestAdvancedFeatureProcessor::test_process`](tests/recursive_training/test_advanced_feature_processor.py) passes.
    *   `pytest -q` shows the test passing.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

### Task GTB10-002
*   **Details:** The `test_process_with_disabled_techniques` failure (mock for `apply_time_frequency_decomposition` not called) was resolved. The `unittest.mock.patch` target in the `with` statement in [`tests/recursive_training/test_advanced_feature_processor.py`](tests/recursive_training/test_advanced_feature_processor.py) was updated to correctly target the function where it is imported and used within the `recursive_training.data.advanced_feature_processor` module (i.e., `'recursive_training.data.advanced_feature_processor.apply_time_frequency_decomposition'`).
*   **Potential Files Involved:**
    *   [`tests/recursive_training/test_advanced_feature_processor.py`](tests/recursive_training/test_advanced_feature_processor.py)
    *   [`recursive_training/data/advanced_feature_processor.py`](recursive_training/data/advanced_feature_processor.py)
    *   [`recursive_training/data/time_frequency_decomposition.py`](recursive_training/data/time_frequency_decomposition.py)
*   **Success Criteria:**
    *   [`tests/recursive_training/test_advanced_feature_processor.py::TestAdvancedFeatureProcessor::test_process_with_disabled_techniques`](tests/recursive_training/test_advanced_feature_processor.py) passes.
    *   `pytest -q` shows the test passing.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

### Task GTB10-003
*   **Details:** The `test_get_cost_summary` failure, initially a floating-point precision issue (fixed with `pytest.approx`), subsequently failed with `KeyError: 'token_usage'`. This was resolved by correcting the key used in the `get_cost_summary` method in [`recursive_training/data/ingestion_manager.py`](recursive_training/data/ingestion_manager.py) to 'token_usage' when populating the per-source summary information.
*   **Potential Files Involved:**
    *   [`tests/recursive_training/test_data_ingestion.py`](tests/recursive_training/test_data_ingestion.py)
    *   [`recursive_training/data/data_ingestion.py`](recursive_training/data/data_ingestion.py) (or `recursive_training/data/ingestion_manager.py`)
*   **Success Criteria:**
    *   [`tests/recursive_training/test_data_ingestion.py::TestRecursiveDataIngestionManager::test_get_cost_summary`](tests/recursive_training/test_data_ingestion.py) passes.
    *   `pytest -q` shows the test passing.
    *   Cost calculations are handled with appropriate precision.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

---

**Considerations for Sprint 10:**
*   The remaining 10 failing tests will be prioritized for subsequent sprints.
*   The 40 warnings from `pytest -q` should be reviewed if time permits.