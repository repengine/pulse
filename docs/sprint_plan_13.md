# Sprint 13 Plan

**Sprint Goal:** Address the final three failing tests in the suite to achieve a fully green build.

**Start Date:** 2025-05-12
**End Date:** 2025-05-13 (Target)

**Sprint Focus:** Various modules including `forecast_engine.ai_forecaster`, `recursive_training.rules.rule_adjustment`, and `trust_system.trust_engine`.

---

## Sprint Backlog

### Task GTB13-001
*   **Details:** The `test_predict_default` failure (AssertionError: non-zero adjustment != 0.0) was resolved. The fix involved patching the module-level `_model` and `_input_size` variables in `forecast_engine.ai_forecaster` within the test `test_predict_default` in [`tests/test_ai_forecaster.py`](tests/test_ai_forecaster.py) to ensure a predictable, controlled environment for the `predict` function call, leading to the expected `0.0` adjustment.
*   **Potential Files Involved:**
    *   Test file: [`tests/test_ai_forecaster.py`](tests/test_ai_forecaster.py)
    *   Source file: [`forecast_engine/ai_forecaster.py`](forecast_engine/ai_forecaster.py)
*   **Success Criteria:**
    *   [`tests/test_ai_forecaster.py::TestAIForecaster::test_predict_default`](tests/test_ai_forecaster.py) passes.
    *   `pytest -q` shows the test passing.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

### Task GTB13-002
*   **Details:** The `test_adjust_rules_from_learning` failure (`AssertionError: register_variable(...) call not found`) was resolved. The fix involved two parts:
    1.  Modifying assertions for `mock_register_variable` in [`tests/test_rule_adjustment.py`](tests/test_rule_adjustment.py) to use `self.assertAlmostEqual` for the 'default' floating-point values.
    2.  Correcting the patch target for `log_variable_weight_change` from `'core.pulse_learning_log.log_variable_weight_change'` to `'trust_system.rule_adjustment.log_variable_weight_change'` to resolve a `mock_log.call_count` assertion error.
*   **Potential Files Involved:**
    *   Test file: [`tests/test_rule_adjustment.py`](tests/test_rule_adjustment.py)
    *   Source file: [`recursive_training/rules/rule_adjustment.py`](recursive_training/rules/rule_adjustment.py)
    *   Source file: [`core/variable_registry.py`](core/variable_registry.py)
*   **Success Criteria:**
    *   [`tests/test_rule_adjustment.py::TestRuleAdjustment::test_adjust_rules_from_learning`](tests/test_rule_adjustment.py) passes.
    *   `pytest -q` shows the test passing.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

### Task GTB13-003
*   **Details:** The `test_compute_risk_score_no_memory` failure (`AssertionError: 0.26 != 0.06`) was resolved. The `compute_risk_score` function in [`trust_system/trust_engine.py`](trust_system/trust_engine.py) was modified to correctly set the `historical_component_value` (used in the weighted sum) to `0.0` when no historical forecasts are available. This aligns with the test's expectation for the 'no memory' scenario and ensures the risk score is calculated correctly under these conditions.
*   **Potential Files Involved:**
    *   Test file: [`tests/test_trust_engine_risk.py`](tests/test_trust_engine_risk.py)
    *   Source file: [`trust_system/trust_engine.py`](trust_system/trust_engine.py) (specifically the `compute_risk_score` function)
*   **Success Criteria:**
    *   [`tests/test_trust_engine_risk.py::TestRiskScoring::test_compute_risk_score_no_memory`](tests/test_trust_engine_risk.py) passes.
    *   `pytest -q` shows the test passing.
    *   No new regressions introduced.
*   **Assigned Agent:** debug
*   **Priority:** High
*   **Status:** Done

---

## Test Suite Status (Start of Sprint 13)

*   Passed: 455
*   Failed: 3
*   Warnings: 40