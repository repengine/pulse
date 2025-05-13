# Sprint 7 Plan

**Sprint Goal:** Address critical blockers in visualization, advanced feature processing, and S3 data storage to improve test pass rates and overall system stability.

## High Priority Blockers

---

**Task ID:** GTB7-001
**Description:** All targeted tests (`test_plot_metrics_dashboard`, `test_plot_metrics_dashboard_no_show`, `test_plot_reliability_diagram`) now pass. The `AttributeError` in `plot_metrics_dashboard` tests was resolved by ensuring the source code in `recursive_training/advanced_metrics/visualization.py` uses NumPy-style tuple indexing (e.g., `axs[0, 0]`) and the test mock in `tests/recursive_training/advanced_metrics/test_visualization.py` correctly provides a NumPy array where each element is a fully configured `MagicMock`.
**Potential Files Involved:**
    *   `tests/recursive_training/advanced_metrics/test_visualization.py`
    *   Likely source file: `recursive_training/advanced_metrics/visualization.py` (or similar module responsible for plotting)
**Success Criteria:**
    *   `tests/recursive_training/advanced_metrics/test_visualization.py::test_plot_metrics_dashboard` passes.
    *   `tests/recursive_training/advanced_metrics/test_visualization.py::test_plot_metrics_dashboard_no_show` passes.
    *   `pytest -q` shows these tests passing.
    *   No new regressions introduced in the visualization module.
**Assigned Agent:** debug
**Priority:** High
**Status:** Done

---

**Task ID:** GTB7-002
**Description:** Tests `TestAdvancedFeatureProcessor::test_process` and `TestAdvancedFeatureProcessor::test_process_with_disabled_techniques` are failing because `apply_time_frequency_decomposition` is not called. The root cause appears to be an underlying issue with TensorFlow/Keras operations within `apply_self_supervised_learning` due to TensorFlow no longer supporting native Windows. This is an environmental/dependency issue, not a direct bug in the Pulse codebase that can be fixed by simple code changes for the native Windows target. The `TypeError` in `SimpleAutoencoder.fit()` was previously addressed, but the TensorFlow compatibility issue prevents successful execution of this component.
**Potential Files Involved:**
    *   `tests/recursive_training/test_advanced_feature_processor.py`
    *   Likely source file: `recursive_training/advanced_feature_processor.py`
**Success Criteria:**
    *   `tests/recursive_training/test_advanced_feature_processor.py::TestAdvancedFeatureProcessor::test_process` passes.
    *   `tests/recursive_training/test_advanced_feature_processor.py::TestAdvancedFeatureProcessor::test_process_with_disabled_techniques` passes.
    *   `pytest -q` shows these tests passing.
    *   The `apply_time_frequency_decomposition` method is correctly called within the `AdvancedFeatureProcessor`.
    *   No new regressions introduced in the advanced feature processing module.
**Assigned Agent:** debug
**Priority:** High
**Status:** Blocked

---

**Task ID:** GTB7-003
**Description:** The `AssertionError: assert 'source' in {}` for `TestS3DataStore::test_retrieve_dataset_s3_direct_read` and `TestS3DataStore::test_retrieve_dataset_s3_with_cache` was resolved by modifying the `retrieve_dataset_s3` method in `recursive_training/data/s3_data_store.py` to correctly include the 'source' key in the returned metadata dictionary. Both tests now pass.
**Potential Files Involved:**
    *   `tests/recursive_training/test_s3_data_store.py`
    *   Likely source file: `recursive_training/s3_data_store.py` (or `recursive_training/data_store.py` if S3 functionality is inherited)
**Success Criteria:**
    *   `tests/recursive_training/test_s3_data_store.py::TestS3DataStore::test_retrieve_dataset_s3_direct_read` passes.
    *   `tests/recursive_training/test_s3_data_store.py::TestS3DataStore::test_retrieve_dataset_s3_with_cache` passes.
    *   `pytest -q` shows these tests passing.
    *   The 'source' key is correctly included in the metadata when datasets are retrieved from `S3DataStore`.
    *   No new regressions introduced in the S3 data store module.
**Assigned Agent:** code
**Priority:** High
**Status:** Done

---