# Pulse Codebase Baseline Report

This report summarizes the baseline state of the Pulse codebase, including test results and potential issues identified from recent analyses.

## Pytest Execution Summary (`pytest -q`)

The `pytest -q` command was executed with the following outcome:

*   **Status:** Interrupted
*   **Errors:** 1 (occurred during test collection)
*   **Warnings:** 5
*   **Total Execution Time:** 72.97 seconds (0:01:12)

## Collection Errors

One error occurred during the test collection phase, preventing a full test run:

*   **File:** `tests/ingestion/test_ingestion_changes.py:223`
*   **Error Type:** `IndentationError`
*   **Message:** `unindent does not match any outer indentation level`
*   **Details:**
    ```
    E     File "C:\Users\natew\Pulse\tests\ingestion\test_ingestion_changes.py", line 223
    E       else:
    E            ^
    E   IndentationError: unindent does not match any outer indentation level
    ```

## Warnings Summary

The following warnings were reported during the `pytest` execution:

1.  **Warning Type:** `PytestCollectionWarning`
    *   **File:** `tests/recursive_training/rules/test_hybrid_adapter.py:115`
    *   **Message:** `cannot collect test class 'TestCondition' because it has a __init__ constructor (from: tests/recursive_training/rules/test_hybrid_adapter.py)`

2.  **Warning Type:** `PytestCollectionWarning`
    *   **File:** `tests/recursive_training/rules/test_hybrid_adapter.py:122`
    *   **Message:** `cannot collect test class 'TestAction' because it has a __init__ constructor (from: tests/recursive_training/rules/test_hybrid_adapter.py)`

3.  **Warning Type:** `PydanticDeprecatedSince20` (Reported 2 times)
    *   **File:** `venv/Lib/site-packages/pydantic/_internal/_config.py:323`
    *   **Message:** `Support for class-based \`config\` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/`

4.  **Warning Type:** `DeprecationWarning`
    *   **File:** `tests/test_digest_exporter.py:3`
    *   **Message:** `foresight_architecture.digest_exporter is deprecated. Use forecast_output.digest_exporter instead.`

## Potential Import Errors

The following potential import error was identified through prior static analysis:

*   **File:** `simulation_engine/simulator_core.py`
*   **Lines:** 72-74
*   **Issue:** Potential unhandled `ImportError` for the module `symbolic_system.symbolic_state_tagger.tag_symbolic_state`.
    *   **Context:** The code attempts to import `tag_symbolic_state` within a `try-except ImportError` block. The concern is whether the `ImportError` is handled appropriately in all scenarios or if this import is critical and should always succeed.
    *   **Relevant Code Snippet (lines 72-74):**
        ```python
        try:
            from symbolic_system.symbolic_state_tagger import tag_symbolic_state
        except ImportError:
            # Further handling or logging of this exception would be expected here
            pass # Placeholder for actual handling
        ```

## Failing Tests

*   An automated scan prior to the `pytest` run did not identify any explicitly marked failing tests.
*   However, the `pytest` execution detailed above was **interrupted by a collection error**. This means that the full suite of tests was not executed, and therefore, the status of individual tests (beyond the collection phase) could not be determined in that run.