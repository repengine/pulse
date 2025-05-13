# Sprint 14 Plan

**Sprint Goal:** Address all outstanding `pytest` warnings to improve code health and future-proof the application. Subsequently, analyze current test coverage and create a plan to achieve 100% test coverage.

**Start Date:** 2025-05-12
**End Date:** 

**Sprint Focus:** Code quality, warning resolution, and test coverage analysis.

---

## Sprint Backlog

### Task GTB14-001: Address PydanticDeprecatedSince20 Warnings
*   **Description:** Multiple `PydanticDeprecatedSince20` warnings indicate that class-based `config` is deprecated and `ConfigDict` should be used instead.
*   **Affected Files (examples from logs):**
    *   `venv\Lib\site-packages\pydantic\_internal\_config.py` (This is within the venv, but the issue originates from project models using the old config style). The actual project files using Pydantic models need to be identified and updated.
*   **Success Criteria:**
    *   All Pydantic models in the project are updated to use `ConfigDict` instead of class-based `config`.
    *   `pytest -q` shows no `PydanticDeprecatedSince20` warnings.
    *   No new regressions introduced.
*   **Assigned Agent:** code
*   **Priority:** Medium
*   **Status:** To Do

### Task GTB14-002: Address PytestReturnNotNoneWarning Warnings
*   **Description:** Multiple `PytestReturnNotNoneWarning` warnings indicate that test functions are returning values instead of using `assert` statements. This will become an error in future pytest versions.
*   **Affected Files (examples from logs):**
    *   [`api_key_test.py`](api_key_test.py)
    *   [`chatmode/test_openai_integration.py`](chatmode/test_openai_integration.py)
    *   [`dev_tools/testing/api_key_test.py`](dev_tools/testing/api_key_test.py)
    *   [`iris/iris_utils/test_historical_data_pipeline.py`](iris/iris_utils/test_historical_data_pipeline.py)
    *   [`iris/test_alpha_vantage.py`](iris/test_alpha_vantage.py)
    *   [`iris/test_github.py`](iris/test_github.py)
    *   [`iris/test_newsapi_direct.py`](iris/test_newsapi_direct.py)
    *   [`iris/test_open_meteo.py`](iris/test_open_meteo.py)
    *   [`iris/test_plugins.py`](iris/test_plugins.py)
    *   [`iris/test_reddit.py`](iris/test_reddit.py)
    *   [`iris/test_reddit_direct.py`](iris/test_reddit_direct.py)
    *   [`iris/test_world_bank.py`](iris/test_world_bank.py)
    *   [`tests/ingestion/test_incremental_ingestion.py`](tests/ingestion/test_incremental_ingestion.py)
    *   [`tests/ingestion/test_ingestion_changes.py`](tests/ingestion/test_ingestion_changes.py)
*   **Success Criteria:**
    *   All identified test functions are modified to use `assert` statements instead of returning values.
    *   `pytest -q` shows no `PytestReturnNotNoneWarning` warnings.
    *   No new regressions introduced.
*   **Assigned Agent:** code
*   **Priority:** Medium
*   **Status:** To Do

### Task GTB14-003: Address datetime.utcnow() Deprecation Warnings
*   **Description:** Multiple `DeprecationWarning` for `datetime.datetime.utcnow()` suggest using `datetime.datetime.now(datetime.UTC)`.
*   **Affected Files (examples from logs):**
    *   [`memory/forecast_memory.py`](memory/forecast_memory.py)
    *   [`memory/trace_memory.py`](memory/trace_memory.py)
    *   [`forecast_output/forecast_summary_synthesizer.py`](forecast_output/forecast_summary_synthesizer.py)
*   **Success Criteria:**
    *   All instances of `datetime.utcnow()` are replaced with `datetime.now(datetime.UTC)`.
    *   `pytest -q` shows no `DeprecationWarning` related to `datetime.utcnow()`.
    *   No new regressions introduced.
*   **Assigned Agent:** code
*   **Priority:** Medium
*   **Status:** To Do

### Task GTB14-004: Address foresight_architecture.digest_exporter Deprecation
*   **Description:** A `DeprecationWarning` in [`tests/test_digest_exporter.py`](tests/test_digest_exporter.py) indicates `foresight_architecture.digest_exporter` is deprecated and `forecast_output.digest_exporter` should be used.
*   **Affected Files:**
    *   [`tests/test_digest_exporter.py`](tests/test_digest_exporter.py)
*   **Success Criteria:**
    *   The import in [`tests/test_digest_exporter.py`](tests/test_digest_exporter.py) is updated to use `forecast_output.digest_exporter`.
    *   `pytest -q` shows no related `DeprecationWarning`.
    *   No new regressions introduced.
*   **Assigned Agent:** code
*   **Priority:** Medium
*   **Status:** To Do

### Task GTB14-005: Analyze Test Coverage and Plan for 100%
*   **Description:** With all tests passing, the next step towards a robust build is to ensure comprehensive test coverage. This task involves analyzing the current test coverage and creating a plan to reach 100%.
*   **Success Criteria:**
    *   A test coverage report is generated (e.g., using `pytest-cov`).
    *   The report is analyzed to identify untested code sections.
    *   A prioritized list of modules/functions requiring new or improved tests is created.
    *   A plan (e.g., subsequent sprint tasks) is drafted to implement these tests.
    *   User approval is obtained for the coverage plan.
*   **Assigned Agent:** architect (for planning), tdd (for potential test writing in subsequent sprints)
*   **Priority:** High
*   **Status:** To Do

---

## Test Suite Status (Start of Sprint 14)

*   Passed: 458
*   Failed: 0
*   Warnings: 40