# Sprint Plan: Green the Build (Sprint 4)

## Sprint Goal
Continue resolving critical errors and warnings, focusing on AttributeErrors and data integrity issues in `recursive_training`, and mock verification failures, to significantly improve build stability.

## Work Items

### GTB4-001
- **Task:** Resolve AttributeErrors in `recursive_training.advanced_metrics`
- **Details:** Investigate and fix `AttributeError`s reported in the `recursive_training.advanced_metrics` module. Prioritize the `AttributeError` in `test_cost_control_integration`. Additionally, verify if previously noted patterns like `'list' object has no attribute 'add'` persist or if similar issues exist, and address them. This involves `AttributeError` exceptions, such as a method being called on an object that does not possess it (e.g., `AttributeError: 'method' object has no attribute '...'`), or incorrect method usage on built-in types (e.g., using `some_list.add(item)` instead of `some_list.append(item)`). These errors indicate fundamental issues in object interaction or API usage.
  - User addressed AttributeErrors in `recursive_training.advanced_metrics` and `tests/recursive_training/advanced_metrics/test_enhanced_metrics.py`. Key tests like `test_cost_control_integration` and `test_track_advanced_iteration` are now passing these specific checks.
- **Priority:** Highest
- **Potential Files Involved:**
  - `tests/recursive_training/advanced_metrics/test_enhanced_metrics.py` (specifically `test_cost_control_integration`)
  - Source code within the `recursive_training/advanced_metrics/` directory.
  - Any modules that `cost_control_integration` or similar functions interact with, leading to the attribute error.
- **Assigned_To:** `code` # Tentative
- **Status:** `Done`
- **Success Criteria:**
  - The specific `AttributeError` in `test_cost_control_integration` within `tests/recursive_training/advanced_metrics/test_enhanced_metrics.py` is resolved, and the test passes.
  - A targeted code review of `recursive_training/advanced_metrics/` and its interactions confirms that common `AttributeError` patterns (e.g., `list.add` instead of `list.append`, calling methods on `None` or incorrect types) related to the reported issues are addressed.
  - All previously failing tests in `tests/recursive_training/advanced_metrics/test_enhanced_metrics.py` due to `AttributeError`s now pass consistently.
  - No new `AttributeError`s are introduced in the `recursive_training.advanced_metrics` module as a result of the changes.

### GTB4-002
- **Task:** Address Data Integrity and Processing Failures in `recursive_training`
- **Details:** Addressed 'dataset format error' in `test_evaluate_offline`, assertion failure in `test_storage_format_selection`, and assertion failure in `test_vectorized_filtering` (by correcting test expectation). The 'missing 'best_model' key' in `test_compare_models_advanced` was confirmed not to be an issue. All targeted data integrity and processing failures for this item are resolved.
- **Priority:** Highest
- **Potential Files Involved:**
  - `tests/recursive_training/advanced_metrics/test_enhanced_metrics.py` (for `test_evaluate_offline`, `test_compare_models_advanced`)
  - Source code within `recursive_training/advanced_metrics/` related to model evaluation and comparison.
  - `tests/recursive_training/test_optimized_data_store.py`
  - Source code for `recursive_training/data/optimized_data_store.py` and related data ingestion/processing modules.
- **Assigned_To:** `code` # Tentative
- **Status:** `Done`
- **Success Criteria:**
    - "Assertion failures in `test_vectorized_filtering` within `tests/recursive_training/test_optimized_data_store.py` are resolved, and the test passes."
    - "The filtering logic in `recursive_training/data/optimized_data_store.py` correctly returns the expected number of items for the `test_vectorized_filtering` scenario."

### GTB4-003
- **Task:** Fix Mock Call Verification Failures in `test_rule_generator.py`
- **Details:** Resolve `AssertionError`s related to mock call verifications in `tests/recursive_training/rules/test_rule_generator.py`. Ensure that the `RuleGenerator` interacts with its dependencies as expected according to the test specifications. `AssertionError`s indicating that mocked objects (dependencies of the `RuleGenerator`) were not called the expected number of times, with the expected arguments, or in the correct sequence. This points to discrepancies in the contract or interaction logic between the `RuleGenerator` and its collaborators. Addressed mock call verification failures in `tests/recursive_training/rules/test_rule_generator.py` by aligning `RuleGenerator` behavior with test expectations. All tests in `test_rule_generator.py` are now passing.
- **Priority:** High
- **Potential Files Involved:**
  - `tests/recursive_training/rules/test_rule_generator.py`
  - `recursive_training/rules/rule_generator.py`
  - The actual modules that are being mocked in `test_rule_generator.py`, to understand the intended interactions.
- **Assigned_To:** `debug` # Tentative
- **Status:** `Done`
- **Success Criteria:**
  - All `AssertionError`s related to mock call verifications (e.g., `assert_called_once_with`, `assert_has_calls`, call count mismatches) in `tests/recursive_training/rules/test_rule_generator.py` are resolved.
  - All tests within `tests/recursive_training/rules/test_rule_generator.py` pass consistently.
  - The interactions between `RuleGenerator` and its mocked dependencies align with the test specifications, either through code changes in the `RuleGenerator` or justified test modifications.
  - No new mock verification failures are introduced.