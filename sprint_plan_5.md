# Sprint Plan: Green the Build (Sprint 5)

## Sprint Goal
Continue resolving critical errors and warnings, focusing on `recursive_training` submodules, gravity explainer tests, and visualization errors, to significantly improve build stability.

## Work Items

### GTB5-001
- **Task:** Resolve Failures in `recursive_training` Submodule (`error_handling`)
- **Details:** Investigated and fixed test failures occurring within the `error_handling` submodule of the `recursive_training` system. All tests in `tests/recursive_training/error_handling/` are now passing.
- **Priority:** Highest
- **Potential Files Involved:**
    *   Code: `recursive_training/error_handling/`
    *   Tests: `tests/recursive_training/error_handling/test_error_handler.py`, `tests/recursive_training/error_handling/test_recovery.py`, `tests/recursive_training/error_handling/test_training_monitor.py`
- **Assigned_To:** `debug` # Tentative
- **Status:** `Done`
- **Success_Criteria:**
    *   All tests within `tests/recursive_training/error_handling/test_error_handler.py` pass.
    *   All tests within `tests/recursive_training/error_handling/test_recovery.py` pass.
    *   All tests within `tests/recursive_training/error_handling/test_training_monitor.py` pass.
    *   The `pytest -q` command shows these specific tests passing.
    *   No new regressions are introduced in this submodule.

### GTB5-004
- **ID:** GTB5-004
- **Task:** Resolve Mock Failures in `tests/recursive_training/test_feature_processor_integration.py`
- **Details:** All tests in `tests/recursive_training/test_feature_processor_integration.py` are failing due to mock expectation issues (e.g., "Expected 'extract_features' to be called once. Called 0 times."). This requires a careful review of mock patching targets and the interaction logic in `recursive_training/data/feature_processor_integration.py`. The core issue is ensuring mocks correctly intercept calls made by the code under test. User addressed mock patching issues in `tests/recursive_training/test_feature_processor_integration.py` by correctly targeting `get_feature_processor` and resetting singleton instances in test `setUp`. All tests in this file are now passing.
- **Priority:** Highest
- **Potential Files Involved:**
    *   Tests: `tests/recursive_training/test_feature_processor_integration.py`
    *   Code: `recursive_training/data/feature_processor_integration.py`, `recursive_training/feature_processor.py`
- **Assigned_To:** `debug` # Tentative
- **Status:** `Done`
- **Success_Criteria:**
    *   All tests within `tests/recursive_training/test_feature_processor_integration.py` pass consistently.
    *   Mocked methods (`extract_features`, `fit`, `transform`, etc.) are correctly patched and verified in the tests.
    *   The `pytest -q` command shows these specific tests passing.
    *   No new regressions are introduced in `recursive_training/data/feature_processor_integration.py` or its tests.
### GTB5-002
- **Task:** Address Failures in `test_gravity_explainer.py`
- **Details:** Debug and resolve the test failures originating from `tests/test_gravity_explainer.py`. The `test_simulation_trace_contains_gravity_details` test is failing with `AssertionError: gravity_correction_details should be in the simulation output`. This indicates the key is missing from the trace, despite previous attempts to preserve it in `simulation_engine/simulator_core.py` and `trust_system/trust_engine.py`. Debug mode resolved the `AssertionError` in `test_simulation_trace_contains_gravity_details` by correcting a mock signature mismatch. All tests in `tests/test_gravity_explainer.py` are now passing.
- **Priority:** High
- **Potential Files Involved:**
  - Code: Modules within `symbolic_system/gravity/`, `simulation_engine/simulator_core.py`, `trust_system/trust_engine.py`.
  - Tests: `tests/test_gravity_explainer.py`.
- **Assigned_To:** `debug`
- **Status:** `Done`
- **Success_Criteria:**
  - All tests within `tests/test_gravity_explainer.py` pass.
  - The `pytest -q` command shows a reduction in failed tests corresponding to the resolution of issues in `tests/test_gravity_explainer.py`.
  - The gravity explainer component functions as expected according to its specifications.
  - No new regressions are introduced in `tests/test_gravity_explainer.py` or related gravity explainer code.

### GTB5-003
- **Task:** Fix Visualization Module Errors and Failures
- **Details:** Resolve the `ValueError` in `test_plot_metrics_dashboard` and the `AssertionError` in `test_plot_reliability_diagram` within the visualization module. Ensuring visualizations are correct is important for monitoring and understanding system performance. Specific issues noted are:
    *   `test_plot_metrics_dashboard` (ValueError) - This is an "Error," which can be more critical.
    *   `test_plot_reliability_diagram` (AssertionError)
- **Priority:** High
- **Potential Files Involved:**
  - Code: Modules within the `visualization/` directory.
  - Tests: The tests `test_plot_metrics_dashboard` and `test_plot_reliability_diagram` (likely methods within a test class in a file like `tests/recursive_training/advanced_metrics/test_visualization.py` or a dedicated test file under `tests/visualization/`).
- **Assigned_To:** `code` # Tentative
- **Status:** `Done`
- **Success_Criteria:**
  - The `ValueError` in the `test_plot_metrics_dashboard` test is resolved, and the test passes.
  - The `AssertionError` in the `test_plot_reliability_diagram` test is resolved, and the test passes.
  - The `pytest -q` command shows these specific tests passing.
  - The corresponding visualization functionalities (metrics dashboard plotting, reliability diagram plotting) produce correct and expected outputs.
  - No new regressions are introduced in the visualization module.